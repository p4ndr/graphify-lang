<#
.SYNOPSIS
Interactive console UI for editing git sparse-checkout (cone mode) folders.

.DESCRIPTION
Discovers all tracked directories in the current git repository - plus
untracked local-only directories that exist on disk but were never
committed anywhere (HEAD or upstream) - and presents them as an expandable
checkbox tree. The user navigates with arrow keys, expands/collapses with
Right/Left, toggles selection with Space, and applies with Enter (or
cancels with Esc). Selecting a parent folder cascades the selection state
to all descendants in the UI; on apply, only the top-most selected
directories are passed to `git sparse-checkout set`, which is sufficient
because cone mode includes descendants implicitly.

Local-only directories (marked with a trailing ` +` in the picker) are new
folders the user created directly in the working tree that git has never
seen before. In cone mode, `git add` refuses paths outside the current
sparse-checkout definition, so a brand-new folder is otherwise invisible to
this tool and impossible to bring into the repo without manually widening
the cone first. Selecting one here adds it to the cone; after applying, the
script offers to `git add` any newly-included local-only paths so they are
staged and ready to commit.

The script enables sparse-checkout cone mode if it is not already active.

.EXAMPLE
cd C:\GitHub\MyRepo
.\git-sp.ps1

Launches the interactive picker preloaded with the current sparse-checkout
selection. Apply with Enter to write the new set via `git sparse-checkout set`.

.NOTES
Requires git 2.25+ (sparse-checkout cone mode) on PATH. Must be run from
anywhere inside a git working tree. Uses only built-in console APIs; no
external UI dependencies. Runs on Windows PowerShell 5.1 and PowerShell 7.x.

Windows execution policy is Restricted by default on client SKUs, so if the
script is blocked run it as `pwsh -ExecutionPolicy Bypass -File .\git-sp.ps1`
(or `powershell -ExecutionPolicy Bypass -File .\git-sp.ps1`), or unblock it
once with `Unblock-File .\git-sp.ps1`.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

# git writes informational messages to stderr (e.g. cone-mode conversion
# warnings). In PowerShell 7.3+ with $PSNativeCommandUseErrorActionPreference
# enabled, any stderr emission from a native command can become a terminating
# error even when the exit code is 0 - disable that here so we can read
# $LASTEXITCODE ourselves and decide what to do.
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -Scope Script -ErrorAction Ignore) {
	$PSNativeCommandUseErrorActionPreference = $false
}

# --- Encoding setup so box-drawing / arrow glyphs render correctly --------
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

# --- Git helpers ---------------------------------------------------------

# Centralised git wrapper.
#
# Two PowerShell-5.1 hazards this works around:
#
#   1. Stderr from a native command becomes an ErrorRecord on PowerShell's
#      error stream. Combined with $ErrorActionPreference = 'Stop' that turns
#      innocuous git warnings (e.g. "warning: unrecognized pattern: '.claude'"
#      emitted during cone-mode init) into terminating exceptions. We merge
#      2>&1 into the pipeline so stderr is captured as ordinary output, then
#      filter ErrorRecord objects out of the returned stdout. $LASTEXITCODE
#      is left intact for the caller to decide what to do.
#
#   2. PowerShell parameter-binder hijack of short git flags. An advanced
#      function (anything with [CmdletBinding()] or any [Parameter()] attr)
#      automatically gets the common parameters: -Verbose, -Debug, -ErrorAction,
#      etc. With prefix-matching enabled, `-d` is bound as `-Debug` *before*
#      it ever reaches a ValueFromRemainingArguments parameter - silently
#      dropping the flag from the git command line. The symptom is e.g.
#      `git ls-tree -r -d --name-only HEAD` being executed as
#      `git ls-tree -r --name-only HEAD`, which returns files instead of
#      directories. To prevent this Invoke-Git is deliberately a *simple*
#      (non-advanced) function: no [CmdletBinding()], no [Parameter()] attrs.
#      Remaining arguments are collected from the automatic $args, which
#      preserves every dash-prefixed token exactly as passed.
function Invoke-Git {
	param([switch]$AllowNonZeroExit)
	$arguments = @($args)
	$prevEAP = $ErrorActionPreference
	$ErrorActionPreference = 'Continue'
	$exit = 0
	try {
		$merged = & git @arguments 2>&1
		$exit = $LASTEXITCODE
		$stdout = @(
			$merged | Where-Object { $_ -isnot [System.Management.Automation.ErrorRecord] } |
				ForEach-Object { [string]$_ }
		)
		if ($exit -ne 0 -and -not $AllowNonZeroExit) {
			$stderr = @(
				$merged | Where-Object { $_ -is [System.Management.Automation.ErrorRecord] } |
					ForEach-Object { $_.Exception.Message }
			) -join [Environment]::NewLine
			throw "git $($arguments -join ' ') exited with code $exit. $stderr"
		}
		return $stdout
	} finally {
		$ErrorActionPreference = $prevEAP
		$global:LASTEXITCODE = $exit
	}
}

function Test-IsGitRepo {
	$null = Invoke-Git -AllowNonZeroExit rev-parse --is-inside-work-tree
	return $LASTEXITCODE -eq 0
}

function Get-GitRoot {
	$root = Invoke-Git -AllowNonZeroExit rev-parse --show-toplevel
	if ($LASTEXITCODE -ne 0 -or -not $root) { return $null }
	return ($root | Select-Object -First 1).Trim()
}

function Get-TrackedDirectories {
	param([string]$Ref = 'HEAD')
	$dirs = Invoke-Git -AllowNonZeroExit ls-tree -r -d --name-only $Ref
	if ($LASTEXITCODE -ne 0) { return @() }
	return @($dirs | Where-Object { $_ })
}

# Top-level blobs (root files) in the given ref. Cone mode always includes
# every root file unconditionally, so these are surfaced for visibility only
# - they appear in the picker as non-toggleable entries.
function Get-RootFiles {
	param([string]$Ref = 'HEAD')
	$entries = Invoke-Git -AllowNonZeroExit ls-tree $Ref
	if ($LASTEXITCODE -ne 0) { return @() }
	# Each line is: "<mode> <type> <hash>\t<name>". Keep blobs only.
	return @(
		$entries | Where-Object { $_ -match '^\d+\s+blob\s+' } |
			ForEach-Object { ($_ -split "`t", 2)[1] } |
			Where-Object { $_ }
	)
}

# Resolves the upstream ref to use for "directories that exist on the remote
# but not yet in local HEAD" enumeration. Prefers the configured @{upstream}
# of the current branch; falls back to origin/HEAD (the remote default
# branch); returns $null if neither is set so the picker falls back cleanly
# to HEAD-only enumeration.
function Get-UpstreamRef {
	$ref = Invoke-Git -AllowNonZeroExit rev-parse --abbrev-ref '@{upstream}'
	if ($LASTEXITCODE -eq 0 -and $ref) {
		$first = ($ref | Select-Object -First 1).Trim()
		if ($first) { return $first }
	}
	$ref = Invoke-Git -AllowNonZeroExit symbolic-ref --short refs/remotes/origin/HEAD
	if ($LASTEXITCODE -eq 0 -and $ref) {
		$first = ($ref | Select-Object -First 1).Trim()
		if ($first) { return $first }
	}
	return $null
}

# Untracked directories that exist on disk but appear in neither HEAD nor
# the upstream ref - i.e. folders the user just created locally and has
# never committed. `git ls-files --others --exclude-standard --directory`
# collapses a wholly-untracked directory tree to its top-most untracked
# entry (trailing '/'; respects .gitignore); loose untracked files at any
# level are listed without a trailing slash and are filtered out here since
# root-level files are always materialised by cone mode regardless of the
# sparse-checkout list, and untracked files inside an already-tracked
# directory need no cone change (their parent directory node already
# exists from Get-TrackedDirectories).
function Get-LocalOnlyDirectories {
	$entries = Invoke-Git -AllowNonZeroExit ls-files --others --exclude-standard --directory
	if ($LASTEXITCODE -ne 0) { return @() }
	return @(
		$entries | Where-Object { $_ -and $_.EndsWith('/') } |
			ForEach-Object { $_.TrimEnd('/') } |
			Where-Object { $_ }
	)
}

function Get-CurrentSparseList {
	# git sparse-checkout list emits cone-mode entries as plain directory
	# paths. If the repo is still in legacy (non-cone) mode the file may
	# contain gitignore-style patterns ('/*', '!/.claude/', '!*/'); drop any
	# such patterns so we only seed the tree from clean directory entries.
	$list = Invoke-Git -AllowNonZeroExit sparse-checkout list
	if ($LASTEXITCODE -ne 0) { return @() }
	return @(
		$list | Where-Object {
			$_ -and
			$_ -notmatch '^\s*[!#]' -and
			$_ -notmatch '[*?\[]' -and
			$_ -notmatch '^/'
		} | ForEach-Object { $_.Trim() }
	)
}

function Test-SparseCheckoutEnabled {
	$v = Invoke-Git -AllowNonZeroExit config core.sparseCheckout
	return ($v | Select-Object -First 1) -eq 'true'
}

function Test-SparseCheckoutCone {
	$v = Invoke-Git -AllowNonZeroExit config core.sparseCheckoutCone
	return ($v | Select-Object -First 1) -eq 'true'
}

# Reads .git/info/sparse-checkout directly (if it exists) and returns $true
# when any line is incompatible with cone mode. Cone mode only permits empty
# lines, comments, and the well-formed boilerplate '/*' and '!/*/' (which
# git itself writes); anything else - leading '!', wildcards in the middle,
# bare filenames like 'CLAUDE.md', etc. - is a legacy non-cone pattern that
# will trigger "warning: unrecognized pattern" on every subsequent git
# operation until cleared.
function Test-SparseCheckoutBroken {
	$repo = Invoke-Git -AllowNonZeroExit rev-parse --git-path info/sparse-checkout
	if ($LASTEXITCODE -ne 0 -or -not $repo) { return $false }
	$file = ($repo | Select-Object -First 1).Trim()
	if (-not (Test-Path -LiteralPath $file)) { return $false }
	foreach ($raw in Get-Content -LiteralPath $file) {
		$line = $raw.Trim()
		if (-not $line) { continue }
		if ($line.StartsWith('#')) { continue }
		if ($line -eq '/*') { continue }
		if ($line -eq '!/*/') { continue }
		if ($line.StartsWith('!')) { return $true }
		if ($line -match '[*?\[]') { return $true }
		if ($line.StartsWith('/')) { return $true }
		# A bare top-level token (no slashes) is also non-cone - cone-mode
		# entries are stored as '/<dir>/' boilerplate pairs, not bare names.
		if ($line -notmatch '/') { return $true }
	}
	return $false
}

# Initialise (or convert) sparse-checkout to cone mode. If the repo is
# currently in non-cone mode with arbitrary gitignore-style patterns, or
# was left in a half-broken state by a previous failed run, `init --cone`
# alone will not clear the offending patterns and git will keep emitting
# "warning: unrecognized pattern" on every command. Disable sparse-checkout
# first (restores the full working tree) and then re-init clean under cone
# mode.
function Initialize-ConeSparseCheckout {
	$sparseOn = Test-SparseCheckoutEnabled
	$coneOn   = Test-SparseCheckoutCone
	$broken   = Test-SparseCheckoutBroken

	if ($sparseOn -and $coneOn -and -not $broken) { return }

	if ($broken) {
		Write-Host 'Detected stale / non-cone patterns in .git/info/sparse-checkout - resetting.' -ForegroundColor Yellow
	} elseif ($sparseOn -and -not $coneOn) {
		Write-Host 'Existing non-cone sparse-checkout config detected - converting to cone mode.' -ForegroundColor Yellow
	} else {
		Write-Host 'Enabling sparse-checkout cone mode...' -ForegroundColor Yellow
	}

	if ($sparseOn) {
		Write-Host '(disabling sparse-checkout first to clear existing patterns)' -ForegroundColor DarkGray
		Invoke-Git sparse-checkout disable | Out-Null
	}

	Invoke-Git sparse-checkout init --cone | Out-Null
}

# --- Tree model ----------------------------------------------------------

function New-TreeNode {
	param($Name, $Path, $Parent, [int]$Depth)
	[pscustomobject]@{
		Name       = $Name
		Path       = $Path
		Parent     = $Parent
		Depth      = $Depth
		Children   = [ordered]@{}
		Expanded   = $false
		Selected   = $false
		# Cone mode always materialises every root-level file regardless of
		# the sparse-checkout list - they cannot be toggled, so the picker
		# renders them with an 'always' state and the Space handler skips
		# them. Tracked for visibility only.
		IsRootFile = $false
		# True when this node was contributed by the upstream tracking
		# branch but does not exist in local HEAD yet. Selecting one queues
		# it in the sparse-checkout list ahead of the next pull.
		IsUpstream = $false
		# True when this node exists only as an untracked directory on
		# local disk - not in HEAD, not upstream. Selecting one widens the
		# cone so the (still untracked) folder can subsequently be `git
		# add`-ed; see Get-SelectedLocalPaths.
		IsLocal    = $false
	}
}

function Build-Tree {
	param(
		[string[]]$HeadDirs        = @(),
		[string[]]$UpstreamDirs    = @(),
		[string[]]$LocalDirs       = @(),
		[string[]]$HeadRootFiles   = @(),
		[string[]]$UpstreamRootFiles = @()
	)

	$root = New-TreeNode -Name '' -Path '' -Parent $null -Depth -1
	$root.Expanded = $true

	# Source-of-truth maps: directory/file -> 'head', 'upstream', or
	# 'local'. HEAD always wins when an entry exists in more than one
	# source; upstream wins over local. A path only reaches 'local' when
	# it is a genuinely new, never-committed-anywhere directory.
	$dirSrc = @{}
	foreach ($d in $HeadDirs)     { if ($d) { $dirSrc[$d] = 'head' } }
	foreach ($d in $UpstreamDirs) { if ($d -and -not $dirSrc.ContainsKey($d)) { $dirSrc[$d] = 'upstream' } }
	foreach ($d in $LocalDirs)    { if ($d -and -not $dirSrc.ContainsKey($d)) { $dirSrc[$d] = 'local' } }

	$fileSrc = @{}
	foreach ($f in $HeadRootFiles)     { if ($f) { $fileSrc[$f] = 'head' } }
	foreach ($f in $UpstreamRootFiles) { if ($f -and -not $fileSrc.ContainsKey($f)) { $fileSrc[$f] = 'upstream' } }

	# Add root-file leaves at depth 0 before directories so they appear at
	# the top of the picker.
	foreach ($file in ($fileSrc.Keys | Sort-Object)) {
		$node = New-TreeNode -Name $file -Path $file -Parent $root -Depth 0
		$node.IsRootFile = $true
		$node.IsUpstream = ($fileSrc[$file] -eq 'upstream')
		$root.Children[$file] = $node
	}

	# Then directories. Each path segment becomes a node; whether any given
	# segment is upstream-only is determined by the source of the longest
	# matching prefix that exists in dirSrc.
	foreach ($dir in ($dirSrc.Keys | Sort-Object)) {
		$parts = $dir -split '/'
		$current = $root
		$accum = ''
		for ($i = 0; $i -lt $parts.Count; $i++) {
			$part = $parts[$i]
			$accum = if ($accum) { "$accum/$part" } else { $part }
			if (-not $current.Children.Contains($part)) {
				$node = New-TreeNode -Name $part -Path $accum -Parent $current -Depth $i
				# A node is upstream-only / local-only if its own full path
				# exists only in that source (HEAD doesn't contain it as a
				# directory at all). Intermediate ancestors stay false
				# unless they were themselves never in HEAD.
				if ($dirSrc.ContainsKey($accum)) {
					$node.IsUpstream = ($dirSrc[$accum] -eq 'upstream')
					$node.IsLocal    = ($dirSrc[$accum] -eq 'local')
				}
				$current.Children[$part] = $node
			}
			$current = $current.Children[$part]
		}
	}
	return $root
}

function Get-VisibleNodes {
	param($Node, [System.Collections.Generic.List[object]]$List)
	foreach ($key in $Node.Children.Keys) {
		$child = $Node.Children[$key]
		$List.Add($child) | Out-Null
		if ($child.Expanded -and $child.Children.Count -gt 0) {
			Get-VisibleNodes -Node $child -List $List
		}
	}
}

function Set-NodeSelected {
	param($Node, [bool]$Value)
	$Node.Selected = $Value
	foreach ($key in $Node.Children.Keys) {
		Set-NodeSelected -Node $Node.Children[$key] -Value $Value
	}
}

# Returns 'all', 'none', or 'partial' for display purposes.
function Get-SelectionState {
	param($Node)
	if ($Node.Children.Count -eq 0) {
		if ($Node.Selected) { return 'all' } else { return 'none' }
	}
	$hasSel = $Node.Selected
	$hasUnsel = -not $Node.Selected
	foreach ($key in $Node.Children.Keys) {
		$s = Get-SelectionState -Node $Node.Children[$key]
		if ($s -eq 'partial') { return 'partial' }
		if ($s -eq 'all') { $hasSel = $true } else { $hasUnsel = $true }
		if ($hasSel -and $hasUnsel) { return 'partial' }
	}
	if ($hasSel) { return 'all' } else { return 'none' }
}

# Collect the minimal set of selected directories - if a parent is selected,
# its descendants are NOT added (cone mode includes them implicitly). Root
# files are skipped entirely: cone mode always includes them, and passing a
# blob path to `git sparse-checkout set` errors with "is not a directory".
function Get-MinimalSelection {
	param($Node, [System.Collections.Generic.List[string]]$Result)
	foreach ($key in $Node.Children.Keys) {
		$child = $Node.Children[$key]
		if ($child.IsRootFile) { continue }
		if ($child.Selected) {
			$Result.Add($child.Path) | Out-Null
		} elseif ($child.Children.Count -gt 0) {
			Get-MinimalSelection -Node $child -Result $Result
		}
	}
}

# Every local-only (untracked, never-committed) node left in the Selected
# state after the interactive loop - i.e. every new folder the user just
# brought into the cone. Unlike Get-MinimalSelection this walks the full
# tree rather than stopping at the first selected ancestor: a local-only
# node's .Selected reflects the final cascaded state regardless of whether
# it was toggled directly or inherited from a selected ancestor (own
# toggle or pre-population both cascade via Set-NodeSelected), so every
# match here is a real untracked path that is now inside the applied cone
# and safe to `git add`.
function Get-SelectedLocalPaths {
	param($Node, [System.Collections.Generic.List[string]]$Result)
	foreach ($key in $Node.Children.Keys) {
		$child = $Node.Children[$key]
		if ($child.IsLocal -and $child.Selected) {
			$Result.Add($child.Path) | Out-Null
		}
		if ($child.Children.Count -gt 0) {
			Get-SelectedLocalPaths -Node $child -Result $Result
		}
	}
}

# --- Rendering -----------------------------------------------------------

function Show-Tree {
	param(
		$Root,
		[int]$Cursor,
		[System.Collections.Generic.List[object]]$Visible,
		[int]$ScrollOffset,
		[int]$MaxRows
	)

	[Console]::SetCursorPosition(0, 0)
	$selCount = 0
	foreach ($n in $Visible) { if ($n.Selected) { $selCount++ } }

	$header1 = 'Git sparse-checkout (cone mode) - multi-select editor'
	$header2 = 'Up/Down: navigate   Right/Left: expand/collapse   Space: toggle   Enter: apply   Esc: cancel'
	$header3 = '[x] included  [ ] excluded  [*] root file (always included)  trailing * = upstream-only (not pulled)  trailing + = local-only (untracked, not yet committed)'
	$header4 = "Selected nodes: $selCount    Visible: $($Visible.Count)    Cursor: $($Cursor + 1)/$($Visible.Count)"
	$sep     = ('-' * 80)

	Write-HostLine $header1 -ForegroundColor Cyan
	Write-HostLine $header2 -ForegroundColor DarkGray
	Write-HostLine $header3 -ForegroundColor DarkGray
	Write-HostLine $header4 -ForegroundColor DarkGray
	Write-HostLine $sep     -ForegroundColor DarkGray

	$end = [Math]::Min($ScrollOffset + $MaxRows, $Visible.Count)
	for ($i = $ScrollOffset; $i -lt $end; $i++) {
		$node   = $Visible[$i]
		$indent = '  ' * $node.Depth
		$state  = Get-SelectionState -Node $node
		$check  = if ($node.IsRootFile) {
			'[*]'
		} else {
			switch ($state) {
				'all'     { '[x]' }
				'partial' { '[~]' }
				default   { '[ ]' }
			}
		}
		$marker = if ($node.Children.Count -gt 0) {
			if ($node.Expanded) { '-' } else { '+' }
		} else { ' ' }

		$label = $node.Name
		if ($node.IsUpstream) { $label = "$label *" }
		if ($node.IsLocal)    { $label = "$label +" }
		$line = "$indent$marker $check $label"

		if ($i -eq $Cursor) {
			Write-HostLine $line -ForegroundColor Black -BackgroundColor Cyan
		} else {
			$color = if ($node.IsRootFile) {
				'DarkGray'
			} elseif ($node.IsUpstream) {
				'DarkCyan'
			} elseif ($node.IsLocal) {
				'DarkYellow'
			} else {
				switch ($state) {
					'all'     { 'Green' }
					'partial' { 'Yellow' }
					default   { 'Gray' }
				}
			}
			Write-HostLine $line -ForegroundColor $color
		}
	}
	# Pad to clear stale lines below the last drawn row.
	$drawn = ($end - $ScrollOffset)
	for ($i = $drawn; $i -lt $MaxRows; $i++) {
		Write-HostLine '' -ForegroundColor Gray
	}
}

# Writes a single padded line that fully overwrites the previous row contents
# at the current cursor position, then advances to the next line.
function Write-HostLine {
	param(
		[string]$Text,
		[ConsoleColor]$ForegroundColor = [ConsoleColor]::Gray,
		[ConsoleColor]$BackgroundColor = $Host.UI.RawUI.BackgroundColor
	)
	$width = [Console]::WindowWidth - 1
	if ($Text.Length -gt $width) { $Text = $Text.Substring(0, $width) }
	$padded = $Text.PadRight($width)
	Write-Host $padded -ForegroundColor $ForegroundColor -BackgroundColor $BackgroundColor
}

# --- Main ----------------------------------------------------------------

if (-not (Get-Command git -CommandType Application -ErrorAction Ignore)) {
	throw 'git was not found on PATH. Install git 2.25+ and reopen the shell.'
}

if (-not (Test-IsGitRepo)) {
	throw 'Not inside a git working tree. Run this script from within a git repository.'
}

$repoRoot = Get-GitRoot
Push-Location $repoRoot
try {
	Initialize-ConeSparseCheckout

	Write-Host 'Enumerating tracked directories and root files...' -ForegroundColor DarkGray
	$headDirs       = Get-TrackedDirectories -Ref 'HEAD'
	$headRootFiles  = Get-RootFiles          -Ref 'HEAD'

	Write-Host 'Scanning working tree for untracked local-only directories...' -ForegroundColor DarkGray
	$localDirs = Get-LocalOnlyDirectories
	if ($localDirs.Count -gt 0) {
		Write-Host "Found $($localDirs.Count) untracked local-only director$(if ($localDirs.Count -eq 1) { 'y' } else { 'ies' })." -ForegroundColor DarkGray
	}

	# Upstream enumeration. When @{upstream} (or origin/HEAD) resolves, union
	# its directories and root files into the picker so the user can see and
	# pre-stage anything that exists on the remote but isn't in local HEAD
	# yet. If neither resolves, fall back silently to HEAD-only.
	$upstreamRef       = Get-UpstreamRef
	$upstreamDirs      = @()
	$upstreamRootFiles = @()
	if ($upstreamRef) {
		Write-Host "Including upstream ref '$upstreamRef' in directory enumeration." -ForegroundColor DarkGray
		$upstreamDirs      = Get-TrackedDirectories -Ref $upstreamRef
		$upstreamRootFiles = Get-RootFiles          -Ref $upstreamRef
	} else {
		Write-Host 'No upstream tracking branch resolved - showing HEAD only.' -ForegroundColor DarkGray
	}

	# The apply-time validation set is the union of HEAD + upstream + local
	# directories. Anything outside this set is rejected before being passed
	# to `git sparse-checkout set`. Local-only dirs are included here too -
	# confirmed via live testing that `sparse-checkout set --skip-checks`
	# accepts a directory that has never been tracked in any ref, so there
	# is no reason to reject the very paths this feature exists to surface.
	$dirs = @($headDirs + $upstreamDirs + $localDirs | Where-Object { $_ } | Sort-Object -Unique)
	if ($dirs.Count -eq 0 -and $headRootFiles.Count -eq 0) {
		throw 'No tracked directories, upstream directories, local-only directories, or root files found. Nothing to configure.'
	}

	$tree = Build-Tree `
		-HeadDirs $headDirs `
		-UpstreamDirs $upstreamDirs `
		-LocalDirs $localDirs `
		-HeadRootFiles $headRootFiles `
		-UpstreamRootFiles $upstreamRootFiles

	# Pre-populate selection from current sparse-checkout list.
	$current = Get-CurrentSparseList
	foreach ($path in $current) {
		$parts = $path -split '/'
		$node = $tree
		$ok = $true
		foreach ($p in $parts) {
			if ($node.Children.Contains($p)) { $node = $node.Children[$p] }
			else { $ok = $false; break }
		}
		if ($ok) {
			Set-NodeSelected -Node $node -Value $true
			# Expand ancestors so the included path is visible on first draw.
			$anc = $node.Parent
			while ($anc) { $anc.Expanded = $true; $anc = $anc.Parent }
		}
	}

	# Ensure top level is expanded.
	$tree.Expanded = $true

	# Interaction loop -----------------------------------------------------
	$cursor = 0
	$scroll = 0
	$apply  = $false
	$quit   = $false

	[Console]::Clear()
	[Console]::CursorVisible = $false
	try {
		while (-not $quit) {
			$visible = [System.Collections.Generic.List[object]]::new()
			Get-VisibleNodes -Node $tree -List $visible

			if ($visible.Count -eq 0) { break }
			if ($cursor -ge $visible.Count) { $cursor = $visible.Count - 1 }
			if ($cursor -lt 0) { $cursor = 0 }

			$headerRows = 5
			$maxRows = [Math]::Max(1, [Console]::WindowHeight - $headerRows - 1)
			if ($cursor -lt $scroll) { $scroll = $cursor }
			if ($cursor -ge $scroll + $maxRows) { $scroll = $cursor - $maxRows + 1 }

			Show-Tree -Root $tree -Cursor $cursor -Visible $visible -ScrollOffset $scroll -MaxRows $maxRows

			$key = [Console]::ReadKey($true)
			switch ($key.Key) {
				'UpArrow'    { if ($cursor -gt 0) { $cursor-- } }
				'DownArrow'  { if ($cursor -lt $visible.Count - 1) { $cursor++ } }
				'Home'       { $cursor = 0 }
				'End'        { $cursor = $visible.Count - 1 }
				'PageUp'     { $cursor = [Math]::Max(0, $cursor - $maxRows) }
				'PageDown'   { $cursor = [Math]::Min($visible.Count - 1, $cursor + $maxRows) }
				'RightArrow' {
					$n = $visible[$cursor]
					if ($n.Children.Count -gt 0 -and -not $n.Expanded) { $n.Expanded = $true }
				}
				'LeftArrow'  {
					$n = $visible[$cursor]
					if ($n.Expanded -and $n.Children.Count -gt 0) {
						$n.Expanded = $false
					} elseif ($n.Parent -and $n.Parent.Depth -ge 0) {
						$idx = $visible.IndexOf($n.Parent)
						if ($idx -ge 0) { $cursor = $idx }
					}
				}
				'Spacebar' {
					$n = $visible[$cursor]
					# Root-level files are always materialised in cone mode
					# regardless of the sparse-checkout list. Toggling them
					# is meaningless and would only confuse the user about
					# what the apply step actually does.
					if (-not $n.IsRootFile) {
						$state = Get-SelectionState -Node $n
						$newVal = ($state -ne 'all')
						Set-NodeSelected -Node $n -Value $newVal
					}
				}
				'Enter'  { $apply = $true; $quit = $true }
				'Escape' { $quit = $true }
			}
		}
	} finally {
		[Console]::CursorVisible = $true
		[Console]::Clear()
	}

	if (-not $apply) {
		Write-Host 'Cancelled. No changes applied.' -ForegroundColor Yellow
		return
	}

	$selected = [System.Collections.Generic.List[string]]::new()
	Get-MinimalSelection -Node $tree -Result $selected

	# Defence in depth: cone-mode `set` aborts with exit 128 the moment any
	# argument is not a directory in HEAD. Validate against the known
	# directory set we enumerated at startup, drop anything that isn't a
	# real directory, and report what was dropped so the user understands
	# the resulting selection. Without this gate a single stray file path
	# would fail the whole apply and leave the repo with cone mode disabled.
	$dirSet = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
	foreach ($d in $dirs) { [void]$dirSet.Add($d) }

	$validSelected = New-Object 'System.Collections.Generic.List[string]'
	$rejected = New-Object 'System.Collections.Generic.List[string]'
	foreach ($s in $selected) {
		if ($dirSet.Contains($s)) { $validSelected.Add($s) } else { $rejected.Add($s) }
	}
	if ($rejected.Count -gt 0) {
		Write-Host "Skipping $($rejected.Count) path(s) that are not tracked, upstream, or local-only directories (cone mode requires directories):" -ForegroundColor Yellow
		foreach ($r in $rejected) { Write-Host "  $r" -ForegroundColor Yellow }
	}

	if ($validSelected.Count -eq 0) {
		Write-Host 'No valid folders selected - restricting sparse-checkout to repository root only.' -ForegroundColor Yellow
		# `set` with zero positional args in cone mode restricts to root files only.
		try {
			Invoke-Git sparse-checkout set | Out-Null
		} catch {
			Write-Host "git sparse-checkout set failed: $($_.Exception.Message)" -ForegroundColor Red
			Write-Host 'Rolling back to a clean cone state...' -ForegroundColor Yellow
			Invoke-Git sparse-checkout disable | Out-Null
			Invoke-Git sparse-checkout init --cone | Out-Null
			throw
		}
	} else {
		Write-Host "Applying sparse-checkout cone with $($validSelected.Count) folder(s):" -ForegroundColor Green
		foreach ($s in $validSelected) { Write-Host "  $s" -ForegroundColor Green }
		# --skip-checks lets us pre-stage upstream-only directories that exist
		# on @{upstream} but not in local HEAD yet, and local-only directories that
		# exist on disk but were never committed to any ref. The script already validated
		# every path against the union of HEAD + upstream + local directory sets, so
		# the existence check git would do is redundant.
		$setArgs = @('sparse-checkout', 'set', '--skip-checks') + $validSelected.ToArray()
		try {
			Invoke-Git @setArgs | Out-Null
		} catch {
			Write-Host "git sparse-checkout set failed: $($_.Exception.Message)" -ForegroundColor Red
			Write-Host 'Rolling back to a clean cone state so the repo is not left with cone-mode disabled...' -ForegroundColor Yellow
			Invoke-Git sparse-checkout disable | Out-Null
			Invoke-Git sparse-checkout init --cone | Out-Null
			throw
		}
	}

	Write-Host ''
	Write-Host 'Current sparse-checkout list:' -ForegroundColor Cyan
	$applied = Invoke-Git -AllowNonZeroExit sparse-checkout list
	foreach ($line in $applied) { Write-Host "  $line" }

	# Widening the cone doesn't track anything by itself - the folder is
	# still untracked, just no longer hidden by sparse-checkout. Offer to
	# `git add` the local-only paths that just came into the cone so the
	# whole "create a folder, get it into the repo" flow finishes here
	# instead of leaving the user to hit the same out-of-cone `git add`
	# error this feature exists to route around.
	$stagedLocal = [System.Collections.Generic.List[string]]::new()
	Get-SelectedLocalPaths -Node $tree -Result $stagedLocal
	if ($stagedLocal.Count -gt 0) {
		Write-Host ''
		Write-Host "The following newly-included path(s) are still untracked (not yet committed anywhere):" -ForegroundColor Cyan
		foreach ($p in $stagedLocal) { Write-Host "  $p" -ForegroundColor Yellow }
		$answer = Read-Host "Stage them now with 'git add' so they're ready to commit? [Y/n]"
		if ($answer -notmatch '^(n|no)$') {
			$addArgs = @('add', '--') + $stagedLocal.ToArray()
			try {
				Invoke-Git @addArgs | Out-Null
				Write-Host "Staged $($stagedLocal.Count) path(s). Review with 'git status' and commit when ready." -ForegroundColor Green
			} catch {
				Write-Host "git add failed: $($_.Exception.Message)" -ForegroundColor Red
				Write-Host 'The cone was still widened successfully - stage manually with git add.' -ForegroundColor Yellow
			}
		} else {
			Write-Host 'Skipped staging. The folder(s) are now in the cone - stage manually with git add when ready.' -ForegroundColor DarkGray
		}
	}
} finally {
	Pop-Location
}
