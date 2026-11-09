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

.PARAMETER Bench
`-Bench test [-Run <id>]` opens the runbook window (WPF, Windows only; exit 2
elsewhere). Answers autosave to
<run worktree>/bench-run/results.json and reopening resumes. `-Bench test` pulls first
(fetch, clean up ingested runs, refresh the run folder); a host-sync or pull error that
leaves the run folder usable is listed with 'Proceed with run? [Y/n]' (-NonInteractive refuses).
Runbook keys (plan 20): `<!-- step: task=T1 type=console expect=/re/ fail=/re/
collect=glob restart=acad|closed|open settled mode=vlx|lsp -->`; mode= (on a step, or under a lane
heading for the whole lane) hides the step in a run of the other load mode, as a settled one.
Log checks (plan 31; no step asks the tester to search a file): `report=<glob>[,<glob>]` (run-relative files
written since the step opened) with `expect=/re/` (each must match a line), `fail=/re/` (a matching line FAILs,
quoted), `count=/re/>=N` or `<=N`, `cases=<id-glob>[,..]` (only those case ids judged, by their status lines
'PASS|FAIL|SKIP|ERROR [NEW|KNOWN] <id>'; SKIP or absent = not run), `allow-skip=<id-glob>[,..]`, `wait=<s>`
(default the larger of 1800 and twice the step's last run), `done=/re/`, `icase`, `since=step|lane|run`
(files written since the step, its lane's first step or the run opened; default step).
Any step type takes them. Without keys the harness
summary '=== X PASS|FAIL ===' and its FAIL lines decide. Complete when a file holds
'BENCH-END lane=<lane> step=<step> status=PASS|FAIL|ERROR' (the test code writes it; every such file is judged),
else the done line; judged anyway with a FAIL after wait=, when AutoCAD exited (with the last 20 lines) or on
Stop. Regex: .NET, case-sensitive unless icase; one regex per key, repeat a key for more; inside /.../ spaces
and | are fine, a slash is \/, and --> is written --\> . The test code learns its step from gsb:step and
gsb:lane (sent first with every Send), bench-run/current-step.txt, or GSB_STEP / GSB_LANE in a Run job.
Fenced powershell blocks get Run,
lisp / acad blocks Send to AutoCAD (COM SendCommand: each Lisp form, or each command line),
open blocks Open (one path per line; drawings in the running AutoCAD), start-acad blocks Start
AutoCAD (the block's command line, else .bench.ini [bench] acad =); every fence gets Copy;
a path in `code` or a link opens when clicked (relative = under the run folder; missing = said
in Output); {run} {main} (backslashes) and {run/} {main/} (forward slashes).
Owner checklist: run `git-sp -Bench test`; the tree has Open / Tester responded (and
Settled, when a step's task is done) with coloured marks; Alt+P/F/B/N, Alt+Left/Right,
Ctrl+Enter work; Run on a powershell block streams into Output and attaches
bench-run/out/<step>-<n>.log; Copy fills the clipboard; a C:\ path in `code` opens Explorer;
with AutoCAD open the status bar shows the last bench load and a step's AutoCAD lines
land in bench-run/out/<step>-acad.log; a step with expect= shows a suggestion; a
restart=closed step with AutoCAD running shows the red banner; Files lists new files with
their step; the region screenshot and Ctrl+V paste attach a PNG; Finish shows the review
page and Push prints 'Pushed bench-results/<run>'.

Bench mode for the test host. `-Bench pull` (also the default verb) fetches,
reads .bench.ini from origin/main, removes the local branch, worktree and
folder of ingested runs, and creates or refreshes the worktree
`<repo>-bench-<run>` (detached at the run tag, same sparse cone as this
checkout) for each open run. `-Bench push` sends untracked files, RESULT.tsv
and bench.patch to the branch bench-results/<run> without touching the worktree.
`-Bench delete [-Run <id>]` (or Del in the run picker) deletes a run everywhere after a
[y/N]: .bench.ini state = dropped on origin/main, the remote branch and tag, the run folder,
local branch and tag; pull then cleans up dropped runs on other hosts.
`-Run`, `-Files`, `-Results` (TSV: task, result, note, with or without a
header row) and `-NonInteractive`
let a script drive both verbs without the picker.

Before pull and test, git-sp runs <main clone>/tools/host-sync.ps1 when that
file exists (in the main clone, not the run worktree), else a `git pull --ff-only`
of the main clone; a failure stops pull and is listed + asked by test. When that
update changes git-sp.ps1 itself, git-sp relaunches the new copy (once).
`-NoHostSync` skips both. After each create or refresh of a run folder, git-sp runs
<main clone>/tools/bench-prepare.ps1 -RunFolder <run folder> -RunId <id> -Main <main clone>
when it exists (e.g. repoint .prv files at the run folder); output in bench-run/prepare.log,
shown in the window header; tracked files it changes stay out of bench.patch; non-zero = error.
Finish runs <main clone>/tools/bench-finish.ps1 (same arguments; e.g. put settings back) before
the review page; its log is bench-run/finish.log, a failure shows in red there. .bench.ini
[bench] vlx = <files> and stamp = <file, line 1 = build>: the status bar shows each VLX's build
(member <x>stamp_<build> in the VLX load list) green / red / amber (no stamp), read again when a
VLX changes. AutoCAD lines of a step that read as errors (; error, Error:, FAIL, bad argument,
not a function, refused) show under the note (Insert into note), fold out on the review page
and are named in the RESULT.tsv note with the step's files.
Nothing stale enters AutoCAD (needs [bench] vlx and stamp). At pull, per vlx file: missing; or no valid
<vlx>.stamp and not tracked in git; or tracked but last committed before the last commit that changed
line 1 of the stamp file: then bench-run/autoload.off is written (line 1 = reason). The bundle loads
nothing (trace NOLOAD, acad-status load=off), the window header turns red, Send to AutoCAD is refused
except Start AutoCAD, and a panel lists the rebuild steps (MAKELISPAPP on the .prv files, quit AutoCAD
fully). Rebuild done is refused while acad.exe runs, checks every vlx file is newer than autoload.off,
writes <vlx>.stamp and deletes autoload.off. A tracked, git-fresh vlx gets its .stamp at pull; an
untracked one never does (nothing proves it). <vlx>.stamp = 3 lines, LF: line 1 the build (line 1 of
the stamp file), line 2 the file's LOCAL LastWriteTime as yyyy-MM-dd HH:mm:ss
(what LISP builds from vl-file-systime), line 3 its size in bytes. The repo's load file must load a VLX only
when the .stamp exists and matches all three.
[bench] lsp = <files> (the repo's uncompiled loaders, e.g. src/ust.lsp, src/ust-test.lsp): the window shows an
Uncompiled sources toggle, on by default; it writes bench-run/load-mode.txt (line 1 lsp|vlx, line 2 the list). The
bundle sets gsb:mode ("lsp"|"vlx") and gsb:lsp (full paths) before the load file, which picks what to load.
Uncompiled mode has no rebuild-first (autoload.off is ignored) and writes bench-run/lsp-src.txt at window start and
Start AutoCAD: line 1 clean|dirty (tracked files against the run's commit), line 2 the commit, line 3 changed files.

Vendoring: a repo carries its own copy (bin/git-sp.ps1, bin/git-sp.cmd); ag-toolbox is the source of truth.
`git-sp -Vendor update -To <repo root> [-From <git url or path>] [-Ref main] [-Commit]` from the source copy, or
`bin/git-sp -Vendor update [-Commit]` from a vendored copy (source and ref from bin/git-sp.vendor), fetches only
those two files (shallow, blobless, sparse), refuses a ps1 that does not parse, and records source, ref, sha and
sha256 in bin/git-sp.vendor. `-Vendor check` exits 1 when the source has a newer commit; -Bench warns at start then.

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
param(
	# -Bench [pull|push]: bench round trip (plan 15). Without -Bench nothing
	# below changes: the sparse-checkout picker runs as before.
	[switch]$Bench,
	[Parameter(Position = 0)][string]$Verb,
	[string]$Run,
	[string[]]$Files,
	[string]$Results,
	[switch]$NonInteractive,
	[switch]$NoHostSync,
	# -Vendor [update|check]: copy git-sp into a repo's bin/ from ag-toolbox (the source of truth), or check it
	[switch]$Vendor,
	[string]$From,
	[string]$To,
	[string]$Ref = 'main',
	[switch]$Commit
)

$ErrorActionPreference = 'Stop'
$script:BenchArgs = @{}; foreach ($k in $PSBoundParameters.Keys) { $script:BenchArgs[$k] = $PSBoundParameters[$k] }   # -Bench relaunch (T66)
$script:BootHash = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm MD5).Hash   # the code now running; a pull that changes the file relaunches it

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
		# tests/archive (bench history): hidden by default, see Set-NodeSelected.
		IsArchive  = $false
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
				if ($accum -match '(^|/)tests/archive$') { $node.IsArchive = $true }
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

# An archive folder is not ticked by a cascade from its parent (one tick on
# the folder itself brings it back); -IncludeArchive is for seeding from the
# existing cone, whose selections are never changed.
function Set-NodeSelected {
	param($Node, [bool]$Value, [switch]$IncludeArchive)
	$Node.Selected = $Value
	foreach ($key in $Node.Children.Keys) {
		$c = $Node.Children[$key]
		if ($Value -and $c.IsArchive -and -not $IncludeArchive) { continue }
		Set-NodeSelected -Node $c -Value $Value -IncludeArchive:$IncludeArchive
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
# True when a selected node has an unticked archive folder below it.
function Test-ArchiveOut {
	param($Node)
	foreach ($key in $Node.Children.Keys) {
		$c = $Node.Children[$key]
		if ($c.IsArchive -and -not $c.Selected) { return $true }
		if ($c.Selected -and (Test-ArchiveOut -Node $c)) { return $true }
	}
	return $false
}

function Get-MinimalSelection {
	param($Node, [System.Collections.Generic.List[string]]$Result)
	foreach ($key in $Node.Children.Keys) {
		$child = $Node.Children[$key]
		if ($child.IsRootFile) { continue }
		if ($child.Selected -and (Test-ArchiveOut -Node $child)) {
			# cone mode cannot exclude a subfolder: list the siblings of the unticked archive instead
			$before = $Result.Count
			Get-MinimalSelection -Node $child -Result $Result
			if ($Result.Count -eq $before) { $Result.Add($child.Path) | Out-Null }  # nothing else below it: keep the folder (and its archive)
		} elseif ($child.Selected) {
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
		if ($node.IsArchive)  { $label = "$label (archive)" }
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

# --- Bench mode (plan 15 S3) ---------------------------------------------

# .bench.ini -> ordered hashtable: section -> hashtable of key -> value.
# '; comment' (own line or after whitespace) is stripped. PS 5.1-safe.
function Read-BenchIni {
	param([string]$Text)
	$ini = [ordered]@{}
	$sec = $null
	foreach ($raw in ($Text -split "`r?`n")) {
		$line = ($raw -replace '(^|\s);.*$', '').Trim()
		if (-not $line -or $line.StartsWith('#')) { continue }
		if ($line -match '^\[(.+)\]$') { $sec = $Matches[1].Trim(); $ini[$sec] = @{}; continue }
		if ($sec -and $line -match '^([^=]+?)\s*=\s*(.*)$') { $ini[$sec][$Matches[1].Trim()] = $Matches[2].Trim() }
	}
	return $ini
}

function Get-BenchIni {
	$t = Invoke-Git -AllowNonZeroExit show origin/main:.bench.ini
	if ($LASTEXITCODE -ne 0) { return $null }
	return (Read-BenchIni -Text ($t -join "`n"))
}

# The id bench_start writes. Every run id from .bench.ini or -Run is checked
# against this before it can reach a path (review 09 H1).
function Test-BenchRunId { param([string]$Id) return ($Id -cmatch '^R[0-9]{8}-[0-9]{4}(-[0-9]+)?\z') }

function Get-BenchRuns {
	param($Ini, [string]$State)
	$out = @()
	foreach ($k in $Ini.Keys) {
		if ($k -eq 'bench' -or $Ini[$k].state -ne $State) { continue }
		if (Test-BenchRunId $k) { $out += $k } else { Write-Host ".bench.ini: section [$k] is not a valid run id; ignored." -ForegroundColor Yellow }
	}
	return $out
}

# -Run, else the id in a run worktree's folder name (never the main checkout,
# whose own name may contain -bench-). Throws on an invalid id.
function Resolve-BenchRunId {
	param([string]$Main, [string]$StartDir)
	$id = ''
	if ($Run) { $id = $Run }
	elseif ($StartDir -ne $Main -and $StartDir -match '-bench-(R[0-9]{8}-[0-9]{4}(-[0-9]+)?)$') { $id = $Matches[1] }
	if ($id -and -not (Test-BenchRunId $id)) { throw "'$id' is not a valid run id (expected R<yyyymmdd>-<hhmm>[-n])." }
	return $id
}

# Main worktree root (the first entry of `worktree list`), even when invoked
# from inside a run worktree. Forward slashes on every host.
function Get-BenchMainRoot {
	[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false   # git prints UTF-8 paths
	$l = @(Invoke-Git worktree list --porcelain)[0]
	return ($l.Substring(9).Trim() -replace '\\', '/')
}

# <parent of Main>/<Main leaf>-bench-<id>; the id is validated and the result must sit next to Main.
function Get-BenchWorktree {
	param([string]$Main, [string]$RunId)
	if (-not (Test-BenchRunId $RunId)) { throw "'$RunId' is not a valid run id (expected R<yyyymmdd>-<hhmm>[-n])." }
	$parent = (Split-Path -Parent $Main) -replace '\\', '/'
	$wt = (Join-Path $parent ((Split-Path -Leaf $Main) + "-bench-$RunId")) -replace '\\', '/'
	if (((Split-Path -Parent $wt) -replace '\\', '/') -ne $parent) { throw "Refusing run folder ${wt}, not next to ${Main}." }
	return $wt
}

# Console checkbox list built on Write-HostLine. Space toggles, Enter accepts,
# Esc cancels ($null). -Single: Enter picks the cursor row only.
function Select-Checklist {
	param([string]$Title, [string[]]$Items, [bool[]]$Ticked, [switch]$Single, [switch]$AllowDelete)
	if ($Items.Count -eq 0) { return @() }
	$on = New-Object 'bool[]' $Items.Count
	for ($i = 0; $i -lt $Items.Count; $i++) { if ($Ticked -and $i -lt $Ticked.Count) { $on[$i] = $Ticked[$i] } }
	$cur = 0; $top = 0; $done = $null
	[Console]::Clear(); [Console]::CursorVisible = $false
	try {
		while ($null -eq $done) {
			$rows = [Math]::Max(1, [Console]::WindowHeight - 4)
			if ($cur -lt $top) { $top = $cur }
			if ($cur -ge $top + $rows) { $top = $cur - $rows + 1 }
			[Console]::SetCursorPosition(0, 0)
			Write-HostLine $Title -ForegroundColor Cyan
			Write-HostLine ('Up/Down: move   Space: toggle   Enter: accept   Esc: cancel' + $(if ($AllowDelete) { '   Del: delete run everywhere' })) -ForegroundColor DarkGray
			Write-HostLine ('-' * 80) -ForegroundColor DarkGray
			for ($r = 0; $r -lt $rows; $r++) {
				$i = $top + $r
				if ($i -ge $Items.Count) { Write-HostLine ''; continue }
				$box = if ($Single) { '   ' } elseif ($on[$i]) { '[x]' } else { '[ ]' }
				if ($i -eq $cur) { Write-HostLine "$box $($Items[$i])" -ForegroundColor Black -BackgroundColor Cyan }
				else { Write-HostLine "$box $($Items[$i])" }
			}
			switch ([Console]::ReadKey($true).Key) {
				'UpArrow'   { if ($cur -gt 0) { $cur-- } }
				'DownArrow' { if ($cur -lt $Items.Count - 1) { $cur++ } }
				'Spacebar'  { $on[$cur] = -not $on[$cur] }
				'Enter'     { $done = @(); if ($Single) { $done = @($Items[$cur]) } else { for ($i = 0; $i -lt $Items.Count; $i++) { if ($on[$i]) { $done += $Items[$i] } } } }
				'Escape'    { $done = $false }
				'Delete'    { if ($AllowDelete) { $done = @{ delete = $Items[$cur] } } }
			}
		}
	} finally { [Console]::CursorVisible = $true; [Console]::Clear() }
	if ($done -is [bool]) { return $null }
	if ($done -is [hashtable]) { return $done }   # -AllowDelete: @{ delete = <item> }
	return @($done)
}

function Set-BenchCone {
	param([string]$Wt, [string[]]$Cone)
	Invoke-Git -C $Wt sparse-checkout init --cone | Out-Null
	Invoke-Git -C $Wt sparse-checkout set --skip-checks @Cone | Out-Null
}

# Create or refresh the run worktree, detached at the run tag.
function Update-BenchWorktree {
	param([string]$Main, [string]$RunId, $Section)
	$wt = Get-BenchWorktree $Main $RunId
	$tag = if ($Section.tag) { $Section.tag } else { "bench/$RunId" }
	$sha = (Invoke-Git rev-parse --verify "refs/tags/$tag^{commit}" | Select-Object -First 1).Trim()
	$sparse = Test-SparseCheckoutEnabled
	$cone = @(Get-CurrentSparseList)
	if (Test-Path -LiteralPath "$wt/.git") {
		if ((Invoke-Git -C $wt rev-parse HEAD | Select-Object -First 1).Trim() -ne $sha) { Invoke-Git -C $wt checkout --detach $sha | Out-Null }
		if ($sparse) { Set-BenchCone -Wt $wt -Cone $cone }
		Write-Host "Refreshed $wt at $tag" -ForegroundColor Green
		Invoke-BenchPrepare -Main $Main -Wt $wt -RunId $RunId
		return
	}
	Invoke-Git worktree add --detach --no-checkout $wt $sha | Out-Null
	if ($sparse) { Set-BenchCone -Wt $wt -Cone $cone }
	Invoke-Git -C $wt checkout --force --detach $sha | Out-Null
	Write-Host "Created $wt at $tag" -ForegroundColor Green
	Invoke-BenchPrepare -Main $Main -Wt $wt -RunId $RunId
}

# Repo hook: <main>/tools/bench-prepare.ps1 -RunFolder <wt> -RunId <id> -Main <main>,
# run from the main clone (current code, so old run tags get it too) after each
# create or refresh of a run folder; -NoHostSync does not skip it. Output goes to
# <wt>/bench-run/prepare.log (the window header shows its last line). Tracked
# files it changes (e.g. .prv files repointed at the run folder) are set
# assume-unchanged, so they stay out of bench.patch and do not count as unpushed.
# ponytail: a tester edit to one of those files is hidden too; list them per run if that matters.
# Non-zero exit throws (pull: error; test: listed + asked).
function Invoke-BenchPrepare {
	param([string]$Main, [string]$Wt, [string]$RunId)
	$hs = "$Main/tools/bench-prepare.ps1"
	if (-not (Test-Path -LiteralPath $hs)) { return }
	$was = @(Invoke-Git -C $Wt diff --name-only HEAD)
	New-Item -ItemType Directory -Force -Path "$Wt/bench-run" | Out-Null
	$ps = (Get-Process -Id $PID).Path
	$o = @(& $ps -NoProfile -ExecutionPolicy Bypass -File $hs -RunFolder $Wt -RunId $RunId -Main $Main 2>&1 | ForEach-Object { "$_" })
	$code = $LASTEXITCODE
	$o += "bench-prepare: exit $code $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
	[IO.File]::WriteAllLines("$Wt/bench-run/prepare.log", [string[]]$o)
	foreach ($l in $o) { Write-Host $l }
	$new = @(Invoke-Git -C $Wt diff --name-only HEAD | Where-Object { $was -notcontains $_ })
	if ($new.Count) { Invoke-Git -C $Wt update-index --assume-unchanged -- @new | Out-Null }
	if ($code -eq 0) { return }
	$plog = Get-BenchFullPath -Dir $Wt -Rel 'bench-run/prepare.log'
	throw "$hs failed (exit $code) for the RUN folder ${Wt}; see $plog."
}

# [bench] vlx = <comma list> -> trimmed names (also read by the window and Invoke-BenchTest).
function Get-BenchVlxList {
	param($Bcfg)
	return @(([string]$Bcfg.vlx) -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}

# Line 1 of the [bench] stamp file in a run folder = the expected build ('' when there is none).
function Get-BenchExpectedStamp {
	param([string]$RunDir, [string]$Stamp)
	if (-not $Stamp -or -not (Test-Path -LiteralPath "$RunDir/$Stamp")) { return '' }
	return ([string]@(Get-Content -LiteralPath "$RunDir/$Stamp")[0]).Trim()
}

# <vlx>.stamp next to each artifact, 3 lines (LF): expected build;
# file local LastWriteTime yyyy-MM-dd HH:mm:ss (what vl-file-systime gives); size in bytes.
# It exists only when the artifact is proven to match the build: the load file checks it before loading the VLX.
function Write-BenchStamp {
	param([string]$RunDir, [string[]]$Vlx, [string]$Stamp)
	$exp = Get-BenchExpectedStamp -RunDir $RunDir -Stamp $Stamp
	foreach ($v in $Vlx) {
		$f = Get-Item -LiteralPath "$RunDir/$v" -ErrorAction SilentlyContinue
		if (-not $f) { continue }
		$t = $f.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
		[IO.File]::WriteAllText("$RunDir/$v.stamp", "$exp`n$t`n$($f.Length)`n")
	}
}

# One artifact has a .stamp that still matches the expected build, the file time and the size.
function Test-BenchStampValid {
	param([string]$RunDir, [string]$Vlx, [string]$Expected)
	$f = Get-Item -LiteralPath "$RunDir/$Vlx" -ErrorAction SilentlyContinue
	if (-not $f -or -not (Test-Path -LiteralPath "$RunDir/$Vlx.stamp")) { return $false }
	$l = @(Get-Content -LiteralPath "$RunDir/$Vlx.stamp")
	$t = $f.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')
	return ($l.Count -ge 3 -and $l[0] -eq $Expected -and $l[1] -eq $t -and $l[2] -eq "$($f.Length)")
}

# For tracked artifacts only: the last commit touching one comes BEFORE the last commit that changed line 1 of the
# stamp file (at the run tag's HEAD in the run folder).
function Test-BenchBuildStale {
	param([string]$Wt, [string]$Stamp, [string[]]$Vlx)
	$lg = @('log', "-L1,1:$Stamp", '-n', '1', '--format=%H')
	$sc = @(Invoke-Git -AllowNonZeroExit -C $Wt @lg | Where-Object { $_ -match '^[0-9a-f]{40}$' })[0]
	if (-not $sc) { return $false }   # stamp not in git: nothing to compare
	$bc = @(Invoke-Git -AllowNonZeroExit -C $Wt log -n 1 --format=%H -- @Vlx | Where-Object { $_ })[0]
	if (-not $bc) { return $true }
	if ($bc -eq $sc) { return $false }
	$mb = @('merge-base', '--is-ancestor', $bc, $sc)
	[void](Invoke-Git -AllowNonZeroExit -C $Wt @mb)
	return ($LASTEXITCODE -eq 0)
}

# [bench] lsp = <comma list>: the repo's uncompiled loaders (ust 2026-11-09); empty = VLX only.
function Get-BenchLspList {
	param($Bcfg)
	return @(([string]$Bcfg.lsp) -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}

# <run>\bench-run\load-mode.txt: line 1 'lsp' (uncompiled sources, the window's default when [bench] lsp is set) or
# 'vlx', line 2 the [bench] lsp list. The bundle reads it before the load file (gsb:mode, gsb:lsp). -> 'lsp' | 'vlx'.
function Get-BenchLoadMode {
	param([string]$RunDir)
	$l = @(Get-Content -LiteralPath "$RunDir/bench-run/load-mode.txt" -ErrorAction Ignore)
	if ($l.Count -ge 2 -and $l[0].Trim() -eq 'lsp' -and $l[1].Trim()) { return 'lsp' }
	return 'vlx'
}

function Write-BenchLoadMode {
	param([string]$RunDir, [string]$Mode, [string[]]$Lsp)
	New-Item -ItemType Directory -Force -Path "$RunDir/bench-run" | Out-Null
	[IO.File]::WriteAllText("$RunDir/bench-run/load-mode.txt", "$Mode`n$($Lsp -join ', ')`n")
}

# Uncompiled mode proves what it loads: <run>\bench-run\lsp-src.txt, line 1 'clean' (no tracked file differs from
# the run's commit) or 'dirty', line 2 the commit, line 3 the changed files. Written at window start and Start AutoCAD.
function Write-BenchLspProof {
	param([string]$RunDir)
	$ga = @('-C', $RunDir, 'rev-parse', 'HEAD'); $head = (@(Invoke-Git -AllowNonZeroExit @ga) -join '').Trim()
	$ga = @('-C', $RunDir, 'status', '--porcelain', '--untracked-files=no'); $ch = @(Invoke-Git -AllowNonZeroExit @ga)
	$ch = @($ch | ForEach-Object { ([string]$_).Substring([Math]::Min(3, ([string]$_).Length)) } | Where-Object { $_ })
	$st = if ($ch.Count) { 'dirty' } else { 'clean' }
	New-Item -ItemType Directory -Force -Path "$RunDir/bench-run" | Out-Null
	[IO.File]::WriteAllText("$RunDir/bench-run/lsp-src.txt", "$st`n$head`n$($ch -join ', ')`n")
	return @{ state = $st; head = $head; changed = $ch }
}

# <run>\bench-run\autoload.off = rebuild-first: line 1 is the reason, its time is when rebuild-first began.
# -> @{ reason; since (UTC) } or $null. Uncompiled mode: never (no VLX is loaded).
function Get-BenchRebuildState {
	param([string]$RunDir)
	if ((Get-BenchLoadMode -RunDir $RunDir) -eq 'lsp') { return $null }
	$f = Get-Item -LiteralPath "$RunDir/bench-run/autoload.off" -ErrorAction SilentlyContinue
	if (-not $f) { return $null }
	return @{ reason = ([string]@(Get-Content -LiteralPath $f.FullName)[0]); since = $f.LastWriteTimeUtc }
}

# Run folder made or pulled. Per [bench] vlx file: fine = a valid .stamp, or tracked in git and committed at or after
# the last change of line 1 of the stamp file (a .stamp is then written); anything else (missing, untracked without a
# valid .stamp, committed before the stamp) = rebuild-first: autoload.off, so the bundle loads nothing.
# No [bench] vlx/stamp keys: nothing. -> 'none' | 'ok' | 'stale'.
# Full, absolute path of a run-relative file, for anything a human reads (owner: never a relative path).
function Get-BenchFullPath {
	param([string]$Dir, [string]$Rel)
	return [IO.Path]::GetFullPath([IO.Path]::Combine($Dir, $Rel))
}

# Same for a list of run-relative entries (Get-BenchUnpushed output: 'tracked changes (bench.patch)' is no path).
function Get-BenchFullList {
	param([string]$Dir, [string[]]$Rel)
	$full = @($Rel | ForEach-Object {
			if ($_ -like 'tracked changes*') { $_ } else { Get-BenchFullPath -Dir $Dir -Rel $_ }
		})
	return ($full -join ', ')
}

# rebuild-first: <run>\bench-run\autoload.off, line 1 = $Why. The file (its time = when rebuild-first began) is
# rewritten only when the reason changes.
function Write-BenchRebuildFirst {
	param([string]$RunDir, [string]$Why)
	New-Item -ItemType Directory -Force -Path "$RunDir/bench-run" | Out-Null
	$was = Get-BenchRebuildState -RunDir $RunDir
	if (-not $was -or $was.reason -ne $Why) { [IO.File]::WriteAllText("$RunDir/bench-run/autoload.off", "$Why`n") }
}

# Why one [bench] vlx no longer matches its .stamp (full paths, both times), '' when it matches.
function Get-BenchVlxDrift {
	param([string]$RunDir, [string]$Vlx, [string]$Expected)
	if (Test-BenchStampValid -RunDir $RunDir -Vlx $Vlx -Expected $Expected) { return '' }
	$f = Get-BenchFullPath -Dir $RunDir -Rel $Vlx
	$item = Get-Item -LiteralPath $f -ErrorAction SilentlyContinue
	if (-not $item) { return "$f is missing" }
	$fmt = 'yyyy-MM-dd HH:mm:ss'
	$mine = "$f is from $($item.LastWriteTime.ToString($fmt)), $($item.Length) bytes"
	if (-not (Test-Path -LiteralPath "$f.stamp")) { return "$mine, and $f.stamp does not exist" }
	$l = @(Get-Content -LiteralPath "$f.stamp")
	if ($l.Count -lt 3) { return "$mine; $f.stamp is incomplete" }
	if ($l[0] -ne $Expected) { return "$mine; $f.stamp is for build $($l[0]), expected $Expected" }
	return "$mine, but $f.stamp (written at Rebuild done) says $($l[1]), $($l[2]) bytes: rebuilt since"
}

# Window start, Start AutoCAD click and tick: a [bench] vlx that no longer matches its .stamp (missing, other time or
# size, other build) puts the run back to rebuild-first. Already rebuild-first: nothing (the start time stays).
# -> $true when it just went back.
function Invoke-BenchRebuildRecheck {
	param([string]$RunDir, [string[]]$Vlx, [string]$Stamp)
	if ((Get-BenchLoadMode -RunDir $RunDir) -eq 'lsp') { [void](Write-BenchLspProof -RunDir $RunDir); return $false }
	if (-not $Vlx.Count -or -not $Stamp) { return $false }
	if (Get-BenchRebuildState -RunDir $RunDir) { return $false }
	$exp = Get-BenchExpectedStamp -RunDir $RunDir -Stamp $Stamp
	$bad = @($Vlx | ForEach-Object { Get-BenchVlxDrift -RunDir $RunDir -Vlx $_ -Expected $exp } | Where-Object { $_ })
	if (-not $bad.Count) { return $false }
	$here = "in this RUN folder $([IO.Path]::GetFullPath($RunDir)) (not the main clone)"
	Write-BenchRebuildFirst -RunDir $RunDir -Why "$($bad -join '; ') $($here): rebuild it here before anything loads"
	return $true
}

function Initialize-BenchBuildState {
	param([string]$Wt, $Bcfg)
	$vlx = Get-BenchVlxList -Bcfg $Bcfg
	$stamp = [string]$Bcfg.stamp
	if (-not $vlx.Count -or -not $stamp) { return 'none' }
	$exp = Get-BenchExpectedStamp -RunDir $Wt -Stamp $stamp
	$trk = @($vlx | Where-Object { @(Invoke-Git -AllowNonZeroExit -C $Wt ls-files -- $_).Count })
	$old = $trk.Count -gt 0 -and (Test-BenchBuildStale -Wt $Wt -Stamp $stamp -Vlx $trk)
	$bad = @(); $old2 = @(); $fresh = @()
	foreach ($v in $vlx) {
		if (Test-BenchStampValid -RunDir $Wt -Vlx $v -Expected $exp) { continue }
		if ((Test-Path -LiteralPath "$Wt/$v") -and $trk -contains $v -and -not $old) { $fresh += $v; continue }
		$bad += $v
		if ($old -and $trk -contains $v) { $old2 += $v }
	}
	$off = "$Wt/bench-run/autoload.off"
	if (-not $bad.Count) {
		Remove-Item -LiteralPath $off -Force -ErrorAction SilentlyContinue
		Write-BenchStamp -RunDir $Wt -Vlx $fresh -Stamp $stamp
		return 'ok'
	}
	$why = @()
	$full = { param($v) Get-BenchFullPath -Dir $Wt -Rel $v }
	if ($old2.Count) { $why += "committed $(($old2 | ForEach-Object { & $full $_ }) -join ', ') predates stamp $exp" }
	$rest = @($bad | Where-Object { $old2 -notcontains $_ })
	if ($rest.Count) {
		$why += "$(($rest | ForEach-Object { & $full $_ }) -join ', ') missing or not built for stamp $exp"
	}
	$here = "in this RUN folder $([IO.Path]::GetFullPath($Wt)) (not the main clone)"
	$why = ($why -join '; ') + " $($here): rebuild it here before anything loads"
	Write-BenchRebuildFirst -RunDir $Wt -Why $why   # start time kept while stale
	foreach ($v in $bad) { Remove-Item -LiteralPath "$Wt/$v.stamp" -Force -ErrorAction SilentlyContinue }
	return 'stale'
}

# Rebuild done: refused while AutoCAD runs or when an artifact is not newer than rebuild-first; else stamps are
# written and rebuild-first ends. -> '' on success, else the refusal text.
function Complete-BenchRebuild {
	param([string]$RunDir, [string[]]$Vlx, [string]$Stamp, [bool]$Running)
	$rs = Get-BenchRebuildState -RunDir $RunDir
	if (-not $rs) { return '' }
	if ($Running) { return 'AutoCAD is running: quit it fully (a loaded VLX cannot be unloaded).' }
	$old = @($Vlx | Where-Object { -not (Test-Path -LiteralPath "$RunDir/$_") })
	foreach ($v in $Vlx) {
		$f = Get-Item -LiteralPath "$RunDir/$v" -ErrorAction SilentlyContinue
		if ($f -and $f.LastWriteTimeUtc -le $rs.since) { $old += $v }
	}
	if ($old.Count) {
		$old = @($old | ForEach-Object { Get-BenchFullPath -Dir $RunDir -Rel $_ })
		return "Not rebuilt since rebuild-first began: $($old -join ', ')"
	}
	Write-BenchStamp -RunDir $RunDir -Vlx $Vlx -Stamp $Stamp
	Remove-Item -LiteralPath "$RunDir/bench-run/autoload.off" -Force
	return ''
}

# Files a run worktree holds that the push carrying $Tip did not (review 09 M1):
# an untracked file not in $Tip as files/<f> with the same content, a result
# row of bench-run/RESULT.tsv not in $Tip's RESULT.tsv, the filled runbook if
# changed, and tracked changes whose diff is not $Tip's bench.patch. Junk (the
# push skip list) and results.json do not count. No $Tip: everything counts.
function Get-BenchUnpushed {
	param([string]$Wt, [string]$Tip, $Section)
	$same = {
		param($Abs, $Obj)
		if (-not $Tip) { return $false }
		$want = Invoke-Git -AllowNonZeroExit -C $Wt rev-parse --verify --quiet "${Tip}:$Obj"
		if ($LASTEXITCODE -ne 0) { return $false }
		$have = Invoke-Git -C $Wt -c core.sparseCheckout=false hash-object --no-filters -- $Abs
		return (([string]($want | Select-Object -First 1)).Trim() -eq ([string]($have | Select-Object -First 1)).Trim())
	}
	$rb = if ($Section -and $Section.runbook) { 'bench-run/' + [IO.Path]::GetFileName([string]$Section.runbook) } else { '' }
	$out = @(); $dirty = $false
	$tok = ((Invoke-Git -C $Wt status --porcelain -z --untracked-files=all) -join '') -split "`0"
	for ($i = 0; $i -lt $tok.Count; $i++) {
		if ($tok[$i].Length -lt 4) { continue }
		$xy = $tok[$i].Substring(0, 2)
		$f = $tok[$i].Substring(3)
		if ($xy -match '[RC]') { $i++ }
		if ($xy -notmatch '^[?]') { $dirty = $true; continue }
		$leaf = $f.Substring($f.LastIndexOf('/') + 1)
		if (@(Get-BenchSkip | Where-Object { $leaf -like $_ }).Count -gt 0) { continue }
		if ($f -eq 'bench-run/results.json') {   # answers given after the last push (no Finish yet) are work too
			$sent = @{}; foreach ($r in @(Get-BenchTipRows -Wt $Wt -Parent $Tip)) { $sent["$($r.step)|$($r.result)"] = $true }
			$st = Import-RunState -Path "$Wt/$f"
			if (@($st.answers.Keys | Where-Object { $st.answers[$_].result -and -not $sent["$_|$($st.answers[$_].result)"] }).Count) { $out += $f }
		} elseif ($f -eq 'bench-run/RESULT.tsv') {
			$key = { param($r) "$($r.step)|$($r.task)|$($r.result)|$($r.note)" }
			$sent = @(Get-BenchTipRows -Wt $Wt -Parent $Tip | ForEach-Object { & $key $_ })
			$mine = @(Read-BenchTsv -Text ([IO.File]::ReadAllText("$Wt/$f", [Text.Encoding]::UTF8)) | Where-Object { $_.result })
			if (@($mine | Where-Object { (& $key $_) -notin $sent }).Count) { $out += $f }
		} elseif ($rb -and $f -eq $rb) {
			if (-not (& $same "$Wt/$f" ([IO.Path]::GetFileName($f)))) { $out += $f }
		} elseif (-not (& $same "$Wt/$f" "files/$f")) { $out += $f }
	}
	if ($dirty) {
		$p = Join-Path ([IO.Path]::GetTempPath()) ("bench-diff-" + [guid]::NewGuid().ToString('N'))
		try {
			Invoke-Git -C $Wt diff --binary "--output=$p" HEAD | Out-Null
			if ((Get-Item -LiteralPath $p).Length -gt 0 -and -not (& $same $p 'bench.patch')) { $out += 'tracked changes (bench.patch)' }
		} finally { Remove-Item -LiteralPath $p -Force -ErrorAction Ignore }
	}
	return $out
}

# Leaf names a push never sends and a pull never counts as unpushed.
function Get-BenchSkip { return @('*.dwl', '*.dwl2', '*.bak', '*.sv$', '*.ac$', '~$*', 'Thumbs.db') }

# Cleanup of an ingested run: local branch, worktree, folder. Never deletes
# work that did not reach origin (review 09 M1): a worktree holding unpushed
# files, or a local branch not contained in what origin had (the tracking ref,
# or the ingested commit .bench.ini records), is kept with a warning.
function Remove-BenchRun {
	param([string]$Main, [string]$RunId, $Section)
	$wt = Get-BenchWorktree $Main $RunId
	$sha = {
		param($Rev)
		if (-not $Rev) { return '' }
		$v = Invoke-Git -AllowNonZeroExit rev-parse --verify --quiet "$Rev^{commit}"
		if ($LASTEXITCODE -eq 0) { return ([string]($v | Select-Object -First 1)).Trim() }
		return ''
	}
	$local = & $sha "refs/heads/bench-results/$RunId"
	$known = @(& $sha "refs/remotes/origin/bench-results/$RunId")
	if ($Section) { $known += @(& $sha ([string]$Section.ingested_sha)), @(& $sha ([string]$Section.ledger_sha)) }
	$known = @($known | Where-Object { $_ })
	$tip = if ($local) { $local } elseif ($known.Count) { $known[0] } else { '' }
	$keep = $false
	$reg = @(Invoke-Git worktree list --porcelain | Where-Object { $_ -like 'worktree *' } | ForEach-Object { $_.Substring(9).Trim() -replace '\\', '/' })
	if ($reg -contains $wt -and (Test-Path -LiteralPath $wt)) {  # only a registered worktree of this repo, still at the run tag, is ever removed; a gone folder is pruned below (N7)
		$tagSha = (Invoke-Git -AllowNonZeroExit rev-parse --verify --quiet "refs/tags/bench/$RunId^{commit}" | Select-Object -First 1)
		$headSha = (Invoke-Git -AllowNonZeroExit -C $wt rev-parse HEAD | Select-Object -First 1)
		$detached = (Invoke-Git -AllowNonZeroExit -C $wt symbolic-ref -q HEAD) -join ''
		$unpushed = @()
		if (-not $tagSha -or -not $headSha -or $tagSha.Trim() -ne $headSha.Trim() -or $detached) {
			Write-Host "$wt is not detached at the tag bench/$RunId; left alone." -ForegroundColor Yellow
		} elseif (($unpushed = @(Get-BenchUnpushed -Wt $wt -Tip $tip -Section $Section)).Count) {
			$keep = $true
			Write-Host "The RUN folder $wt holds work that never reached origin ($(Get-BenchFullList -Dir $wt -Rel $unpushed)); left alone. Send it with a new run (bench-start), or delete the folder by hand." -ForegroundColor Yellow
		} else {
			Invoke-Git -AllowNonZeroExit worktree remove --force $wt | Out-Null
			# no Remove-Item fallback: on Windows PowerShell 5.1 it follows junctions into their targets
			if (Test-Path -LiteralPath $wt) { Write-Host "$wt is still there: close open files and run pull again." -ForegroundColor Yellow }
		}
	} elseif (Test-Path -LiteralPath $wt) {
		Write-Host "$wt is not a registered worktree of this repo; left alone." -ForegroundColor Yellow
	}
	Invoke-Git -AllowNonZeroExit worktree prune | Out-Null
	if ($local -and -not $keep) {
		$pushed = $false
		foreach ($k in $known) { $null = Invoke-Git -AllowNonZeroExit merge-base --is-ancestor $local $k; if ($LASTEXITCODE -eq 0) { $pushed = $true; break } }
		if ($pushed) { Invoke-Git branch -D "bench-results/$RunId" | Out-Null }
		else { $keep = $true; Write-Host "Local branch bench-results/$RunId holds a commit that never reached origin; kept. Send it with a new run, or delete it with git branch -D." -ForegroundColor Yellow }
	}
	if (-not $keep) { Write-Host "Cleaned up ingested run $RunId" -ForegroundColor DarkGray }
}

function Select-BenchRun {
	param([string[]]$Runs, [string]$Wanted)
	if ($Wanted) {
		if (-not (Test-BenchRunId $Wanted)) { throw "'$Wanted' is not a valid run id (expected R<yyyymmdd>-<hhmm>[-n])." }
		return @($Wanted)
	}
	if ($Runs.Count -le 1 -or $NonInteractive -or [Console]::IsInputRedirected) { return $Runs }
	while ($true) {
		$pick = Select-Checklist -Title 'Open bench runs - choose one' -Items $Runs -Single -AllowDelete
		if ($null -eq $pick) { return @() }
		if ($pick -isnot [hashtable]) { return $pick }
		$ini = Get-BenchIni
		if (Remove-BenchRunEverywhere -Main (Get-BenchMainRoot) -RunId $pick.delete -Section $(if ($ini) { $ini[$pick.delete] })) { $Runs = @($Runs | Where-Object { $_ -ne $pick.delete }) }
		else { Read-Host 'Enter to go back to the list' | Out-Null }
		if ($Runs.Count -le 1) { return $Runs }
	}
}

# --- Delete a run everywhere (owner, 2026-11-04) ----------------------------
# .bench.ini text with [<run>] state = dropped (other lines and newlines kept;
# a missing state line is added under the header). $null: no such section.
function Set-BenchIniDropped {
	param([string]$Text, [string]$RunId)
	$nl = if ($Text.Contains("`r`n")) { "`r`n" } else { "`n" }
	$lines = @($Text -split "`r?`n"); $in = $false; $hit = $false; $done = $false; $out = New-Object System.Collections.ArrayList
	foreach ($l in $lines) {
		if ($l -match '^\s*\[(.+)\]\s*$') {
			if ($in -and -not $done) { [void]$out.Add('state   = dropped'); $done = $true }
			$in = ($Matches[1].Trim() -eq $RunId); if ($in) { $hit = $true }
		} elseif ($in -and -not $done -and $l -match '^\s*state\s*=') { [void]$out.Add('state   = dropped'); $done = $true; continue }
		[void]$out.Add($l)
	}
	if (-not $hit) { return $null }
	if ($in -and -not $done) {   # section is last: add before trailing blank lines
		$i = $out.Count; while ($i -gt 0 -and -not ([string]$out[$i - 1]).Trim()) { $i-- }
		$out.Insert($i, 'state   = dropped')
	}
	return ($out -join $nl)
}

# Commit [<run>] state = dropped onto origin/main from a temp index (no
# checkout, the main clone's index and branch untouched) and push it as a
# fast-forward; a moved main is fetched and retried, never forced.
function Publish-BenchIniDrop {
	param([string]$RunId)
	for ($try = 1; $try -le 3; $try++) {
		Invoke-Git fetch origin main | Out-Null
		$base = (Invoke-Git rev-parse --verify 'refs/remotes/origin/main^{commit}' | Select-Object -First 1).Trim()
		$new = Set-BenchIniDropped -Text ((Invoke-Git show "${base}:.bench.ini") -join "`n") -RunId $RunId
		if ($null -eq $new) { Write-Host ".bench.ini on origin/main has no [$RunId]; nothing to drop there." -ForegroundColor Yellow; return }
		$tmp = Join-Path ([IO.Path]::GetTempPath()) ("bench-ini-" + [guid]::NewGuid().ToString('N'))
		$idx = "$tmp.idx"; $old = $env:GIT_INDEX_FILE
		try {
			[IO.File]::WriteAllText($tmp, $new, (New-Object System.Text.UTF8Encoding $false))
			$blob = (Invoke-Git hash-object -w --no-filters -- $tmp | Select-Object -First 1).Trim()
			$env:GIT_INDEX_FILE = $idx
			Invoke-Git -c index.sparse=false read-tree $base | Out-Null
			Invoke-Git -c index.sparse=false update-index --cacheinfo "100644,$blob,.bench.ini" | Out-Null
			$tree = (Invoke-Git -c index.sparse=false write-tree | Select-Object -First 1).Trim()
		} finally {
			$env:GIT_INDEX_FILE = $old
			Remove-Item -LiteralPath $tmp, $idx -Force -ErrorAction SilentlyContinue
		}
		$ct = @('commit-tree', $tree, '-p', $base, '-m', "bench: drop run $RunId (git-sp -Bench delete)")
		$commit = (Invoke-Git @ct | Select-Object -First 1).Trim()
		$null = Invoke-Git -AllowNonZeroExit push origin "${commit}:refs/heads/main"
		if ($LASTEXITCODE -eq 0) { Write-Host ".bench.ini on origin/main: [$RunId] state = dropped" -ForegroundColor Green; return }
		Write-Host "Push to main rejected (attempt $try of 3); fetching and retrying." -ForegroundColor Yellow
	}
	throw "Could not push the .bench.ini drop of $RunId to origin/main after 3 attempts (never forced); nothing else was deleted."
}

# Delete a run everywhere: .bench.ini state = dropped on origin/main, the
# remote branch bench-results/<run> and tag bench/<run>, then the local run
# folder (worktree), branch and tag. Lists what goes, including work that
# never reached origin, and asks [y/N]; -NonInteractive needs -Run.
function Remove-BenchRunEverywhere {
	param([string]$Main, [string]$RunId, $Section)
	if (-not (Test-BenchRunId $RunId)) { throw "'$RunId' is not a valid run id (expected R<yyyymmdd>-<hhmm>[-n])." }
	Invoke-Git -AllowNonZeroExit fetch --prune --tags origin | Out-Null
	$wt = Get-BenchWorktree $Main $RunId
	$has = { param($Ref) $null = Invoke-Git -AllowNonZeroExit rev-parse --verify --quiet $Ref; $LASTEXITCODE -eq 0 }
	$remoteBranch = & $has "refs/remotes/origin/bench-results/$RunId"
	$items = @(".bench.ini on origin/main: [$RunId] state = dropped")
	if ($remoteBranch) { $items += "remote branch bench-results/$RunId" }
	if (& $has "refs/tags/bench/$RunId") { $items += "tag bench/$RunId (origin and local)" }
	if (Test-Path -LiteralPath $wt) { $items += "run folder $wt" }
	if (& $has "refs/heads/bench-results/$RunId") { $items += "local branch bench-results/$RunId" }
	$lost = @()
	if (Test-Path -LiteralPath "$wt/.git") {
		$tip = if ($remoteBranch) { (Invoke-Git rev-parse "refs/remotes/origin/bench-results/$RunId" | Select-Object -First 1).Trim() } else { '' }
		$lost = @(Get-BenchUnpushed -Wt $wt -Tip $tip -Section $Section)
	}
	Write-Host "Delete run $RunId everywhere:" -ForegroundColor Yellow
	foreach ($i in $items) { Write-Host "  - $i" }
	if ($lost.Count) {
		$lostFull = Get-BenchFullList -Dir $wt -Rel $lost
		Write-Host "  NOT pushed, lost for good (in the RUN folder $wt): $lostFull" -ForegroundColor Red
	}
	if (-not ($NonInteractive -or [Console]::IsInputRedirected)) {
		$a = Read-Host "Delete run $RunId everywhere? [y/N]"
		if ($a -notmatch '^\s*[yY]') { Write-Host 'Not deleted.'; return $false }
	} elseif (-not $Run) { throw '-NonInteractive delete needs -Run <id>.' }
	Publish-BenchIniDrop -RunId $RunId
	if ($remoteBranch) { $null = Invoke-Git -AllowNonZeroExit push origin --delete "refs/heads/bench-results/$RunId"; if ($LASTEXITCODE) { Write-Host "Could not delete the remote branch bench-results/$RunId." -ForegroundColor Yellow } }
	$null = Invoke-Git -AllowNonZeroExit push origin --delete "refs/tags/bench/$RunId"
	if (Test-Path -LiteralPath $wt) {
		$null = Invoke-Git -AllowNonZeroExit worktree remove --force --force $wt
		# no Remove-Item fallback: on Windows PowerShell 5.1 it follows junctions into their targets
		if (Test-Path -LiteralPath $wt) { Write-Host "$wt is still there: close open files (AutoCAD) and delete the folder by hand." -ForegroundColor Yellow }
	}
	Invoke-Git -AllowNonZeroExit worktree prune | Out-Null
	$null = Invoke-Git -AllowNonZeroExit branch -D "bench-results/$RunId"
	$null = Invoke-Git -AllowNonZeroExit tag -d "bench/$RunId"
	Write-Host "Run $RunId deleted." -ForegroundColor Green
	return $true
}

function Invoke-BenchPull {
	param([string]$Main)
	Invoke-Git fetch --prune --tags | Out-Null
	$ini = Get-BenchIni
	if (-not $ini) { Write-Host 'No .bench.ini on origin/main.' -ForegroundColor Yellow; return @() }
	foreach ($r in @(Get-BenchRuns $ini 'ingested') + @(Get-BenchRuns $ini 'dropped')) {
		try { Remove-BenchRun -Main $Main -RunId $r -Section $ini[$r] }
		catch { Write-Host "Could not clean up run $r : $($_.Exception.Message)" -ForegroundColor Yellow }  # e.g. a file still open in AutoCAD
	}
	$open = Get-BenchRuns $ini 'open'
	$script:BenchPicked = @(Select-BenchRun -Runs $open -Wanted $Run | Where-Object { $_ })   # no open run: $null, not one null entry
	$errs = @()
	foreach ($r in $script:BenchPicked) {
		try {
			Update-BenchWorktree -Main $Main -RunId $r -Section $ini[$r]
			$rw = Get-BenchWorktree -Main $Main -RunId $r
			# [bench] lsp = set: uncompiled is the default, before anything reads the rebuild state (ust R20261109-0735)
			$lsp = Get-BenchLspList -Bcfg $ini['bench']
			if ($lsp.Count -and -not (Test-Path -LiteralPath "$rw/bench-run/load-mode.txt")) {
				Write-BenchLoadMode -RunDir $rw -Mode 'lsp' -Lsp $lsp
			}
			$bs = Initialize-BenchBuildState -Wt $rw -Bcfg $ini['bench']
			if ($bs -eq 'stale' -and (Get-BenchLoadMode -RunDir $rw) -eq 'vlx') {
				$off = Get-BenchFullPath -Dir (Get-BenchWorktree -Main $Main -RunId $r) -Rel 'bench-run/autoload.off'
				$msg = "$r : VLX stale or missing: rebuild first, in the RUN folder (autoload.off is $off)"
				Write-Host $msg -ForegroundColor Yellow
			}
		} catch { $errs += "$r : $($_.Exception.Message)" }
	}
	if ($errs.Count) { throw ($errs -join '; ') }   # every picked run is still refreshed first
	return $open
}

# '**' crosses folders, '*' and '?' do not; a pattern without '/' matches the file name.
function Test-BenchGlob {
	param([string]$Rel, [string]$Pattern)
	$re = '^' + ([regex]::Escape($Pattern) -replace '\\\*\\\*', '.*' -replace '\\\*', '[^/]*' -replace '\\\?', '[^/]') + '$'
	if ($Pattern -notmatch '/') { $Rel = $Rel.Substring($Rel.LastIndexOf('/') + 1) }
	return ($Rel -match $re)
}

# RESULT.tsv: step, task, result, note, files. Rows need task/result/note
# (step defaults to task). The pushed file list rides on the first row.
# The T41 runbook GUI calls this with its own rows. Plain TSV, never CSV
# (review 09 N1): fields escape \ tab CR LF as \\ \t \r \n; Read-BenchTsv
# and bench.py _tsv undo it. The header's 6th cell `v2` marks that format
# (L3); a file without it is v1, raw (keep in step with TSV_VERSION in bench.py).
function Write-BenchResult {
	param([string]$Path, $Rows, [string[]]$Files = @())
	$clean = { param($v) ([string]$v).Replace('\', '\\').Replace("`t", '\t').Replace("`r", '\r').Replace("`n", '\n') }
	$lines = @("step`ttask`tresult`tnote`tfiles`tv2")
	$list = $Files -join ','
	$rows = @($Rows)
	if ($rows.Count -eq 0) { $rows = @([pscustomobject]@{ step = '-'; task = ''; result = ''; note = '' }) }
	foreach ($r in $rows) {
		$step = if ($r.step) { $r.step } else { $r.task }
		$lines += (@((& $clean $step), (& $clean $r.task), (& $clean $r.result), (& $clean $r.note), (& $clean $list)) -join "`t")
		$list = ''
	}
	[IO.File]::WriteAllText($Path, (($lines -join "`n") + "`n"), (New-Object System.Text.UTF8Encoding $false))
}

# Orphan-branch commit built without touching the run worktree or any real
# index: GIT_INDEX_FILE points at a temp file, blobs go straight into the
# object store, and only refs/heads/bench-results/<run> moves. That branch is never
# checked out anywhere, so (unlike learning 2089, a temp-index commit onto a
# branch that IS checked out in a shared checkout) no real index is left
# holding stale blobs. Returns the commit sha.
function New-BenchCommit {
	param([string]$Wt, [string]$RunId, [string[]]$Rel, [string]$ResultFile, [string]$PatchFile, [string]$Parent, [string]$Runbook)
	$idx = Join-Path ([IO.Path]::GetTempPath()) ("bench-idx-" + [guid]::NewGuid().ToString('N'))
	$old = $env:GIT_INDEX_FILE
	$env:GIT_INDEX_FILE = $idx
	try {
		$add = {
			param($Abs, $As)
			$sha = (Invoke-Git -C $Wt -c core.sparseCheckout=false hash-object -w --no-filters -- $Abs | Select-Object -First 1).Trim()
			Invoke-Git -C $Wt -c core.sparseCheckout=false -c index.sparse=false update-index --add --cacheinfo "100644,$sha,$As" | Out-Null
		}
		if ($Parent) {  # earlier pushes stay: start from the tip's tree; this push's RESULT.tsv/bench.patch replace theirs
			Invoke-Git -C $Wt -c core.sparseCheckout=false -c index.sparse=false read-tree $Parent | Out-Null
			if (-not $PatchFile) { Invoke-Git -C $Wt -c core.sparseCheckout=false -c index.sparse=false rm --cached --ignore-unmatch -q -- bench.patch | Out-Null }
		}
		foreach ($f in $Rel) { & $add "$Wt/$f" "files/$f" }
		& $add $ResultFile 'RESULT.tsv'
		if ($PatchFile) { & $add $PatchFile 'bench.patch' }
		if ($Runbook) { & $add $Runbook ([IO.Path]::GetFileName($Runbook)) }
		$tree = (Invoke-Git -C $Wt -c core.sparseCheckout=false -c index.sparse=false write-tree | Select-Object -First 1).Trim()
	} finally {
		$env:GIT_INDEX_FILE = $old
		if (Test-Path -LiteralPath $idx) { Remove-Item -LiteralPath $idx -Force }
	}
	$ct = @('-C', $Wt, 'commit-tree', $tree, '-m', "bench $RunId")
	if ($Parent) { $ct += @('-p', $Parent) }
	return (Invoke-Git @ct | Select-Object -First 1).Trim()
}

# RESULT.tsv text -> rows {step, task, result, note, files}, the way bench.py
# _tsv reads it: split on tab (no quoting), a header row when the first cell is
# step or task, else task, result, note (5 columns: step ... files). The
# format is the file's own, never its path (review 09 L2/L3): a header whose
# 6th cell is v2 was written by Write-BenchResult and is unescaped; anything
# else is v1, raw (a tester's own file). A newer version is refused, so a
# push never merges into a tip it cannot read.
function Read-BenchTsv {
	param([string]$Text)
	$lines = @($Text -split "`n" | ForEach-Object { $_.TrimEnd("`r") } | Where-Object { $_.Trim() })
	if (-not $lines.Count) { return @() }
	$head = @($lines[0].Split("`t") | ForEach-Object { $_.Trim().ToLower() })
	$Escaped = $false
	if ($head[0] -in 'task', 'step') {
		$lines = @($lines | Select-Object -Skip 1)
		if ($head.Count -gt 5 -and $head[5] -match '^v[0-9]+$') {
			if ($head[5] -notin 'v1', 'v2') { throw "RESULT.tsv format $($head[5]) is newer than this git-sp (v2): update git-sp." }
			$Escaped = ($head[5] -eq 'v2')
		}
	}
	elseif ($head.Count -lt 5) { $head = 'task', 'result', 'note' }
	else { $head = 'step', 'task', 'result', 'note', 'files' }
	$map = @{ 't' = "`t"; 'n' = "`n"; 'r' = "`r"; '\' = '\' }
	foreach ($ln in $lines) {
		$c = $ln.Split("`t")
		$o = [ordered]@{ step = ''; task = ''; result = ''; note = ''; files = '' }
		for ($i = 0; $i -lt $head.Count -and $i -lt $c.Count; $i++) {
			$v = $c[$i].Trim()
			if ($Escaped) { $v = [regex]::Replace($v, '\\([tnr\\])', { param($m) $map[$m.Groups[1].Value] }) }
			if ($o.Contains($head[$i])) { $o[$head[$i]] = $v }
		}
		if (-not $o.step) { $o.step = $o.task }
		[pscustomobject]$o
	}
}

# Rows of the branch tip's RESULT.tsv that carry a result (the files carrier row has none).
function Get-BenchTipRows {
	param([string]$Wt, [string]$Parent)
	if (-not $Parent) { return @() }
	$null = Invoke-Git -AllowNonZeroExit -C $Wt cat-file -e "${Parent}:RESULT.tsv"
	if ($LASTEXITCODE -ne 0) { return @() }
	$txt = (Invoke-Git -C $Wt show "${Parent}:RESULT.tsv") -join "`n"
	return @(Read-BenchTsv -Text $txt | Where-Object { $_.result })
}

# Rows typed at the prompt, saved to $Save before anything is pushed (review
# 09 L7): an offline failure keeps them for the next push, which reads the file.
function Read-BenchPromptRows {
	param([string]$Tasks, [string]$Save, [string]$RunDir = '', [string]$Stamp = '')
	$rows = @()
	$sf = if ($RunDir) { Get-Item -LiteralPath "$RunDir/bench-run/acad-status.txt" -ErrorAction SilentlyContinue }
	# plan 30 S1 (ust review M5): AutoCAD wrote a status for this run, so a PASS needs the bench judge
	$jd = if ($sf) { @(Get-BenchPassBlock -RunDir $RunDir -Stamp $Stamp -Touched $true) } else { @() }
	foreach ($t in @($Tasks -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })) {
		$a = Read-Host "$t result [p]ass / [f]ail / [Enter] skip"
		if ($a -notmatch '^[pf]') { continue }
		$ra = Resolve-BenchAnswer -Result $(if ($a -match '^p') { 'pass' } else { 'fail' }) -Block $jd
		if (-not $ra.result) { Write-Host $ra.message; $a = 'f' }
		$rows += [pscustomobject]@{ step = $t; task = $t; result = $(if ($a -match '^p') { 'pass' } else { 'fail' }); note = (Read-Host "$t note") }
	}
	if ($rows.Count) {
		New-Item -ItemType Directory -Path (Split-Path -Parent $Save) -Force | Out-Null
		Write-BenchResult -Path $Save -Rows $rows
	}
	return $rows
}

# Tools that run in the main clone (host-sync, acad-run, ...) leave their logs
# there. Before a push, every file in the main clone that matches `collect` or
# *.log, is new, changed or git-ignored, and was written since the run folder
# was opened (its tag), comes into the run folder at the same path: an untracked or
# ignored file is MOVED, a changed tracked file is COPIED (main keeps it).
# Since the run was opened (its tag's commit), else since the run folder was made: host-sync logs come before the folder.
function Get-BenchSince {
	param([string]$Wt, [string]$Tag)
	$since = (Get-Item -LiteralPath "$Wt/.git" -Force).LastWriteTimeUtc.AddMinutes(-1)
	$ct = Invoke-Git -AllowNonZeroExit log -1 --format=%ct "refs/tags/$Tag" | Select-Object -First 1
	if ($LASTEXITCODE -eq 0 -and "$ct" -match '^\d+$') { $t = [DateTime]::new(1970, 1, 1, 0, 0, 0, [DateTimeKind]::Utc).AddSeconds([double]$ct); if ($t -lt $since) { $since = $t } }
	return $since
}

# Logs written during this run into ANOTHER run folder of the same repo (AutoCAD
# still had an older run loaded, R20261104-1006): not sent, named so the owner sees the miss.
function Find-BenchStrayLogs {
	param([string]$Main, [string]$Wt, [string[]]$Collect, [datetime]$Since)
	$pats = @(@($Collect) + 'logs/*.log' | Where-Object { $_ } | Select-Object -Unique)
	$parent = Split-Path -Parent $Main
	foreach ($d in @(Get-ChildItem -LiteralPath $parent -Directory -Filter ((Split-Path -Leaf $Main) + '-bench-R*') -ErrorAction SilentlyContinue)) {
		$root = $d.FullName -replace '\\', '/'
		if ($root -eq $Wt) { continue }
		foreach ($g in $pats) {
			$pre = (($g -split '[*?]')[0]); $pre = if ($pre -match '/') { $pre.Substring(0, $pre.LastIndexOf('/')) } else { '' }
			$dir = if ($pre) { "$root/$pre" } else { $root }
			if (-not (Test-Path -LiteralPath $dir -PathType Container)) { continue }
			foreach ($fi in @(Get-ChildItem -LiteralPath $dir -Recurse:([bool]($g -match '\*\*')) -File -Force -ErrorAction SilentlyContinue)) {
				$f = ($fi.FullName -replace '\\', '/').Substring($root.Length + 1)
				if ($fi.LastWriteTimeUtc -ge $Since -and (Test-BenchGlob $f $g)) { "$root/$f" }
			}
		}
	}
}

function Move-BenchMainLogs {
	param([string]$Main, [string]$Wt, [string[]]$Collect, [string]$Tag)
	if (-not (Test-Path -LiteralPath "$Wt/.git")) { return }
	$since = Get-BenchSince -Wt $Wt -Tag $Tag
	$pats = @(@($Collect) + '*.log' | Where-Object { $_ } | Select-Object -Unique)
	# host-sync runs before the pull that opens the run: its logs count from an hour before (ust 5ffde25)
	$hsSince = $since.AddHours(-1)
	# traditional + all: files inside an ignored folder are listed one by one (matching lists only the folder)
	$tok = ((Invoke-Git -C $Main status --porcelain -z --untracked-files=all --ignored=traditional) -join '') -split "`0"
	$moved = 0; $copied = 0
	for ($i = 0; $i -lt $tok.Count; $i++) {
		if ($tok[$i].Length -lt 4) { continue }
		$xy = $tok[$i].Substring(0, 2); $f = $tok[$i].Substring(3)
		if ($xy -match '[RC]') { $i++; continue }
		if ($xy -match 'D') { continue }
		if (@($pats | Where-Object { Test-BenchGlob $f $_ }).Count -eq 0) { continue }
		$src = "$Main/$f"
		if (-not (Test-Path -LiteralPath $src -PathType Leaf)) { continue }
		$fi = Get-Item -LiteralPath $src -Force
		$from = if ($fi.Name -like '*host-sync*') { $hsSince } else { $since }
		if ($fi.LastWriteTimeUtc -lt $from) { continue }
		$dst = "$Wt/$f"
		if (Test-Path -LiteralPath $dst) {
			if ((Get-FileHash -LiteralPath $dst).Hash -eq (Get-FileHash -LiteralPath $src).Hash) { if ($xy -match '[?!]') { Remove-Item -LiteralPath $src -Force }; continue }
			$dst = (Split-Path -Parent $dst) + '/' + [IO.Path]::GetFileNameWithoutExtension($dst) + '-main' + [IO.Path]::GetExtension($dst)   # one suffix (a -replace on '(\.ext)?$' also hits the empty end match)
		}
		New-Item -ItemType Directory -Path (Split-Path -Parent $dst) -Force | Out-Null
		if ($xy -match '[?!]') { Move-Item -LiteralPath $src -Destination $dst -Force; $moved++ }
		else { Copy-Item -LiteralPath $src -Destination $dst -Force; $copied++ }
	}
	if ($moved -or $copied) { Write-Host "Logs from the main clone $Main into the RUN folder ${Wt}: $moved moved, $copied copied (tracked, left in main)." -ForegroundColor Green }
}

# The files a push sends (plan 20 S6: shared by Invoke-BenchPush and the window's
# review page). Moves main-clone logs in first. -> @{ cand; collect; since; strays; refused }
function Get-BenchPushPlan {
	param([string]$Main, [string]$Wt, $Sec, [string]$RunId)
	$wt = $Wt; $sec = $Sec; $runId = $RunId
	# untracked files, plus modified tracked files that match `collect`; modified
	# tracked files in general travel in bench.patch only.
	$collect = @(([string]$sec.collect) -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
	Move-BenchMainLogs -Main $Main -Wt $wt -Collect $collect -Tag $(if ($sec.tag) { $sec.tag } else { "bench/$runId" })
	$skip = Get-BenchSkip
	$tok = ((Invoke-Git -C $wt status --porcelain -z --untracked-files=all) -join '') -split "`0"
	$cand = @(); $refused = @()
	for ($i = 0; $i -lt $tok.Count; $i++) {
		if ($tok[$i].Length -lt 4) { continue }
		$xy = $tok[$i].Substring(0, 2)
		$f = $tok[$i].Substring(3)
		if ($xy -match '[RC]') { $i++ }
		$hit = @($collect | Where-Object { Test-BenchGlob $f $_ }).Count -gt 0
		if ($xy -notmatch '^[?]' -and ($xy -match 'D' -or -not $hit)) { continue }
		if ($f -in 'bench-run/RESULT.tsv', 'bench-run/results.json') { continue }
		if ($sec.runbook -and $f -eq 'bench-run/' + [IO.Path]::GetFileName([string]$sec.runbook)) { continue }
		$leaf = $f.Substring($f.LastIndexOf('/') + 1)
		if (@($skip | Where-Object { $leaf -like $_ }).Count -gt 0) { continue }
		$len = (Get-Item -LiteralPath "$wt/$f").Length
		if ($len -gt 95MB) { $refused += "$f : $([int]($len / 1MB)) MB"; continue }
		$cand += $f
	}
	# collect also takes matching files git does not list (ignored by any .gitignore, global ones too)
	$seen = @{}; foreach ($c in $cand) { $seen[$c] = $true }
	# plus any *.log written since the run tag anywhere in the run folder (UST fell back to src/ when logs/ was missing, R20261104-1006)
	$since = Get-BenchSince -Wt $wt -Tag $(if ($sec.tag) { $sec.tag } else { "bench/$runId" })
	# plus every file under logs/ and tests/logs/ that git does not track, whenever and by whichever AutoCAD it was
	# written (ust 5ffde25: UST.LOG, PROGRESS, crumb and trench .txt files were left behind)
	foreach ($g in @(@($collect) + '*.log' + 'logs/**' + 'tests/logs/**')) {
		$pre = (($g -split '[*?]')[0]); $pre = if ($pre -match '/') { $pre.Substring(0, $pre.LastIndexOf('/')) } else { '' }
		$dir = if ($pre) { "$wt/$pre" } else { $wt }
		if (-not (Test-Path -LiteralPath $dir -PathType Container)) { continue }
		$tracked = @{}; foreach ($t in @(Invoke-Git -AllowNonZeroExit -C $wt ls-files -- $(if ($pre) { $pre } else { '.' }))) { $tracked[$t] = $true }
		foreach ($fi in @(Get-ChildItem -LiteralPath $dir -Recurse -File -Force -ErrorAction SilentlyContinue)) {
			$f = $fi.FullName.Substring($wt.Length + 1) -replace '\\', '/'
			if ($f.StartsWith('.git/') -or $f.StartsWith('bench-run/') -or $seen[$f] -or $tracked[$f] -or -not (Test-BenchGlob $f $g)) { continue }
			if ($g -eq '*.log' -and $fi.LastWriteTimeUtc -lt $since -and @($collect | Where-Object { Test-BenchGlob $f $_ }).Count -eq 0) { continue }
			if (@($skip | Where-Object { $fi.Name -like $_ }).Count -gt 0) { continue }
			if ($fi.Length -gt 95MB) { $refused += "$f : $([int]($fi.Length / 1MB)) MB"; continue }
			$seen[$f] = $true; $cand += $f
		}
	}
	# every attached file and all of bench-run/files go, even when a .gitignore covers them (R20261104-1504: *.dwg)
	$att = @(foreach ($fi in @(Get-ChildItem -LiteralPath "$wt/bench-run/files" -Recurse -File -Force -ErrorAction SilentlyContinue)) { 'bench-run/files/' + ($fi.FullName.Substring("$wt/bench-run/files".Length + 1) -replace '\\', '/') })
	if (Test-Path -LiteralPath "$wt/bench-run/results.json") { $st = Import-RunState -Path "$wt/bench-run/results.json"; foreach ($k in @($st.answers.Keys)) { $att += @($st.answers[$k].files) } }
	$att += 'bench-run/acad-status.txt', 'bench-run/load-result.txt'   # what AutoCAD loaded: evidence for every run (ust 2026-11-06)
	# one load result per drawing (ust T403.1)
	$lr = @(Get-ChildItem -LiteralPath "$wt/bench-run" -Filter 'load-result-*.txt' -File -ErrorAction Ignore)
	$att += @($lr | ForEach-Object { "bench-run/$($_.Name)" })
	foreach ($f in $att) {
		if (-not $f -or $seen[$f] -or $f.StartsWith('.git/') -or $f -in 'bench-run/RESULT.tsv', 'bench-run/results.json') { continue }
		$fi = Get-Item -LiteralPath "$wt/$f" -Force -ErrorAction SilentlyContinue; if (-not $fi -or $fi.PSIsContainer) { continue }
		if ($fi.Length -gt 95MB) { $refused += "$f : $([int]($fi.Length / 1MB)) MB"; continue }
		$seen[$f] = $true; $cand += $f
	}
	$strays = @(Find-BenchStrayLogs -Main $Main -Wt $wt -Collect $collect -Since $since | Select-Object -Unique)
	$refused = @($refused | ForEach-Object {
			$i = $_.LastIndexOf(' : ')
			(Get-BenchFullPath -Dir $wt -Rel $_.Substring(0, $i)) + $_.Substring($i)
		})
	return @{ cand = $cand; collect = $collect; since = $since; strays = $strays; refused = $refused }
}

function Invoke-BenchPush {
	param([string]$Main, [string]$StartDir)
	Invoke-Git -AllowNonZeroExit fetch origin | Out-Null   # a fresh .bench.ini (M1); offline goes on with the last one
	$ini = Get-BenchIni
	if (-not $ini) { throw 'No .bench.ini on origin/main. Run -Bench pull first.' }
	$runId = Resolve-BenchRunId -Main $Main -StartDir $StartDir
	if (-not $runId) {
		$runId = @(Select-BenchRun -Runs (Get-BenchRuns $ini 'open'))[0]
		if (-not $runId) { throw 'No run chosen. Use -Run <id>.' }
	}
	if (-not $ini.Contains($runId)) { throw "Run $runId is not in .bench.ini." }
	$sec = $ini[$runId]
	if ($sec.state -eq 'ingested') { throw "Run $runId is already ingested (closed); nothing was pushed. Ask for a new run with bench-start and push there (review 09 M1)." }
	$wt = Get-BenchWorktree $Main $runId
	if (-not (Test-Path -LiteralPath "$wt/.git")) { throw "No worktree $wt. Run -Bench pull first." }

	$plan = Get-BenchPushPlan -Main $Main -Wt $wt -Sec $sec -RunId $runId
	$cand = @($plan.cand); $collect = @($plan.collect)
	foreach ($r in $plan.refused) { Write-Host "Refused $r : over the 95 MB limit (git hosts reject larger files)." -ForegroundColor Yellow }
	if ($collect.Count) { Write-Host "collect ($($collect -join ', ')): $(@($cand | Where-Object { $f = $_; @($collect | Where-Object { Test-BenchGlob $f $_ }).Count }).Count) file(s) matched in the RUN folder $wt" }
	foreach ($c in $cand) { Write-Host "  send: $(Get-BenchFullPath -Dir $wt -Rel $c)" }
	foreach ($x in $plan.strays) {
		Write-Host "  NOT sent (in another run folder; copy it into $wt to send it): $x" -ForegroundColor Yellow
	}
	$tick = @($cand | ForEach-Object { $true })   # all candidates start ticked

	# adapter output (RESULT.tsv written into the run folder) replaces the prompt
	$resultsFile = $Results
	$adapter = if ($sec.adapter) { $sec.adapter } elseif ($ini.Contains('bench')) { $ini['bench'].adapter } else { $null }
	if (-not $resultsFile -and (Test-Path -LiteralPath "$wt/bench-run/RESULT.tsv")) { $resultsFile = "$wt/bench-run/RESULT.tsv" }
	$filledRb = $null
	if ($sec.runbook -and (Test-Path -LiteralPath "$wt/bench-run/$([IO.Path]::GetFileName([string]$sec.runbook))")) { $filledRb = "$wt/bench-run/$([IO.Path]::GetFileName([string]$sec.runbook))" }
	if (-not $resultsFile -and $adapter -and (Test-Path -LiteralPath "$wt/RESULT.tsv")) {
		$resultsFile = "$wt/RESULT.tsv"
		$cand = @($cand | Where-Object { $_ -ne 'RESULT.tsv' })
	}

	if ($Files) { $sel = @($cand | Where-Object { $Files -contains $_ }) }
	elseif ($NonInteractive -or [Console]::IsInputRedirected) { $sel = $cand }
	else {
		$pick = Select-Checklist -Title "Files to send for $runId" -Items $cand -Ticked $tick
		if ($null -eq $pick) { Write-Host 'Cancelled.' -ForegroundColor Yellow; return }
		$sel = @($pick)
	}

	$pst = if ($ini -and $ini.Contains('bench')) { [string]$ini['bench'].stamp } else { '' }
	$rows = @()
	if ($resultsFile) {
		# UTF-8 (5.1 reads BOM-less files as ANSI otherwise); escaped or raw per the file's own header (L2)
		$rows = @(Read-BenchTsv -Text ([IO.File]::ReadAllText($resultsFile, [Text.Encoding]::UTF8)) | Where-Object { $_.task -or $_.result })
	} elseif (-not ($NonInteractive -or [Console]::IsInputRedirected)) {
		$rows = @(Read-BenchPromptRows -Tasks ([string]$sec.tasks) -Save "$wt/bench-run/RESULT.tsv" -RunDir $wt -Stamp $pst)
	}
	# plan 30 S1 (ust review M6c): every PASS row of a step that used AutoCAD is judged again at push. Trust boundary: a
	# hand-written RESULT.tsv for steps with no AutoCAD slice is taken as written.
	$pjs = Import-RunState -Path "$wt/bench-run/results.json"
	$pjm = @(Invoke-BenchPushJudge -Rows $rows -RunDir $wt -Stamp $pst -State $pjs)
	foreach ($m in $pjm) { Write-Host "bench judge: $m" }

	$work = Join-Path ([IO.Path]::GetTempPath()) ("bench-" + [guid]::NewGuid().ToString('N'))
	New-Item -ItemType Directory -Path $work | Out-Null
	try {
		$resultFile = "$work/RESULT.tsv"
		Write-BenchResult -Path $resultFile -Rows $rows -Files $sel
		$patch = "$work/bench.patch"
		Invoke-Git -C $wt diff --binary "--output=$patch" HEAD | Out-Null
		if (-not (Test-Path -LiteralPath $patch) -or (Get-Item -LiteralPath $patch).Length -eq 0) { $patch = $null }

		$ok = $false
		for ($try = 1; $try -le 3 -and -not $ok; $try++) {
			if ($try -gt 1) { Invoke-Git -AllowNonZeroExit fetch origin | Out-Null }  # offline: end on "Could not push", not a fetch error
			$parent = $null
			foreach ($ref in "refs/remotes/origin/bench-results/${runId}", "refs/heads/bench-results/${runId}") {
				$p = Invoke-Git -AllowNonZeroExit rev-parse --verify --quiet "$ref^{commit}"
				if ($LASTEXITCODE -eq 0) { $parent = ($p | Select-Object -First 1).Trim(); break }
			}
			# a push MERGES its rows into the branch's RESULT.tsv: earlier results stay, the same step+task is replaced
			$old = @(Get-BenchTipRows -Wt $wt -Parent $parent)
			if ($old.Count) {
				$mine = @($rows | ForEach-Object { "$(if ($_.step) { $_.step } else { $_.task })|$($_.task)" })
				$keep = @($old | Where-Object { "$(if ($_.step) { $_.step } else { $_.task })|$($_.task)" -notin $mine })
				Write-BenchResult -Path $resultFile -Rows (@($rows) + @($keep)) -Files $sel
			}
			$commit = New-BenchCommit -Wt $wt -RunId $runId -Rel $sel -ResultFile $resultFile -PatchFile $patch -Parent $parent -Runbook $filledRb
			Invoke-Git update-ref "refs/heads/bench-results/${runId}" $commit | Out-Null
			$null = Invoke-Git -AllowNonZeroExit push origin "refs/heads/bench-results/${runId}:refs/heads/bench-results/${runId}"
			$ok = ($LASTEXITCODE -eq 0)
			if (-not $ok) { Write-Host "Push rejected (attempt $try of 3); fetching and retrying." -ForegroundColor Yellow }
		}
		if (-not $ok) { throw "Could not push bench-results/$runId after 3 attempts (never forced)." }
		# no runbook window on this run: bench-run/RESULT.tsv holds typed rows, now on origin; the next push asks again
		if (-not $sec.runbook -and -not $Results) { Remove-Item -LiteralPath "$wt/bench-run/RESULT.tsv" -Force -ErrorAction Ignore }
		Write-Host "Pushed bench-results/$runId : $($sel.Count) file(s)$(if ($patch) { ' + bench.patch' }), $($rows.Count) result row(s)." -ForegroundColor Green
	} finally {
		Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction Ignore
	}
}

# --- Runbook GUI (plan 15 S7, T41) ----------------------------------------
# Part 1 is plain PowerShell (tested on Linux): runbook parser, markdown ->
# HTML, results.json, RESULT.tsv rows, filled runbook. Part 2 is the WPF
# window, loaded only on Windows.

# Runbook markdown -> @{ groups; steps }. `## id. title` = group, `### id. title`
# = step; `**Result:**` lines are the answer slot (dropped from the shown body);
# `<!-- step: task=T205.3 push=file -->` gives the step's task and push file;
# `**Required state:** text` gives a lane's or step's required host state.
# Step heading pattern (keep in step with STEP_HEAD in bench.py). The em/en dash
# are built from char codes: the file stays ASCII, which Windows PowerShell 5.1
# would otherwise read as Windows-1252 and break the class (review 09 N4).
function Get-BenchStepHead {
	return '^(#{2,3})\s+(?:(\S+?)\.|((?-i:[A-Z0-9])[\w-]*)(?::|\s+[' + [char]0x2014 + [char]0x2013 + '-]))\s+(.*?)\s*$'
}

# Plan 20 marker keys after task=/push=: type=manual|console|auto|look,
# expect=/re/ (repeatable, all must match), fail=/re/ (any match = FAIL),
# collect=glob[,glob], restart=acad|closed|open, settled (bare word).
# A regex is /.../ with \/ for a slash; spaces are allowed inside it.
function Get-RunbookMarkerKeys {
	$k = @('task', 'push', 'type', 'expect', 'fail', 'collect', 'restart', 'settled', 'made-by', 'timeout')
	# plan 31 log checks and the load-mode key (keep in step with MARKER_KEYS in repo-docs bench.py)
	return $k + @('report', 'done', 'count', 'cases', 'allow-skip', 'wait', 'icase', 'mode', 'since')
}
function Set-RunbookStepKeys {
	param($Step, [string]$Meta)
	# /re/ keys (plan 31): expect, fail, done, count (with >=N or <=N); a slash inside is \/
	$rx = '(expect|fail|done|count)=/((?:\\/|[^/])*)/(?:(>=|<=)(\d+))?'
	foreach ($m in [regex]::Matches($Meta, $rx)) {
		$v = $m.Groups[2].Value.Replace('\/', '/')
		switch ($m.Groups[1].Value) {
			'expect' { $Step.expect += $v }
			'fail' { $Step.fail += $v }
			'done' { $Step.done = $v }
			'count' {
				$op = if ($m.Groups[3].Success) { $m.Groups[3].Value } else { '>=' }
				$n = if ($m.Groups[4].Success) { [int]$m.Groups[4].Value } else { 1 }
				$Step.counts += @{ re = $v; op = $op; n = $n }
			}
		}
	}
	$rest = [regex]::Replace($Meta, $rx, '')
	if ($rest -match '(?:^|\s)type=(manual|console|auto|semi|look)\b') { $Step.type = $Matches[1] }
	if ($rest -match '(?:^|\s)timeout=([1-9]\d{0,4})(?=\s|$)') { $Step.timeout = [int]$Matches[1] }   # S11: seconds
	if ($rest -match '(?:^|\s)collect=(\S+)') { $Step.collect = @($Matches[1] -split ',' | Where-Object { $_ }) }
	if ($rest -match '(?:^|\s)restart=(acad|closed|open)\b') { $Step.restart = $Matches[1] }
	if ($rest -match '(?:^|\s)settled(?:\s|$)') { $Step.settled = $true }
	if ($rest -match '(?:^|\s)report=(\S+)') { $Step.report = $Matches[1] }   # report file globs, comma list
	if ($rest -match '(?:^|\s)cases=(\S+)') { $Step.cases = @($Matches[1] -split ',' | Where-Object { $_ }) }
	if ($rest -match '(?:^|\s)allow-skip=(\S+)') { $Step.allowskip = @($Matches[1] -split ',' | Where-Object { $_ }) }
	if ($rest -match '(?:^|\s)wait=([1-9]\d{0,5})(?=\s|$)') { $Step.wait = [int]$Matches[1] }
	if ($rest -match '(?:^|\s)icase(?:\s|$)') { $Step.icase = $true }
	if ($rest -match '(?:^|\s)mode=(vlx|lsp)(?:\s|$)') { $Step.mode = $Matches[1] }   # load mode the step or lane needs
	if ($rest -match '(?:^|\s)since=(step|lane|run)(?:\s|$)') { $Step.since = $Matches[1] }   # report= files from when
}

# --- plan 31: the log parser (owner 2026-11-09) ----------------------------------------------------------------
# One parser for every text the bench judges: AutoCAD command-line output, AutoCAD logs, console output of a job,
# and any log the bench or a test writes. Steps drive it with marker keys (Set-RunbookStepKeys): report=<glob>[,..]
# expect=/re/ fail=/re/ count=/re/>=N|<=N cases=<glob>[,..] allow-skip=<glob>[,..] wait=<s> done=/re/ icase.
# .NET regex, case-sensitive unless icase. It writes BENCH lines; the BENCH verdict does the rest.

# A BENCH reason: no ';' or backslash, one space, at most 120 characters.
function ConvertTo-BenchReason {
	param([string]$Text)
	$t = (([string]$Text) -replace '[;\\]', ' ' -replace '\s+', ' ').Trim()
	return $t.Substring(0, [Math]::Min(120, $t.Length))
}

# The two harness line shapes the parser knows (functions, not script variables: tests load functions only).
# A status line: optional indent, PASS|FAIL|SKIP|ERROR, optional NEW|KNOWN, then the case id. A summary line:
# '=== NAME PASS|FAIL === ...'.
function Get-BenchCaseRx { '^\s*(PASS|FAIL|SKIP|ERROR)(?:\s+(?:NEW|KNOWN))?\s+(\S+)' }
function Get-BenchSummaryRx { '^\s*=== \S+ (PASS|FAIL) ===' }
# AutoCAD lines that read as errors (ust 24): the error bar under the note, the review, RESULT.tsv, the auto verdict.
function Get-BenchErrorRx { '; error|Error:|FAIL|bad argument|not a function|refused' }
# The Output tab's marks: '!!' for these (a FAIL word, not FAILED inside a word), 'ok' for PASS / loaded.
function Get-BenchConsoleFailRx { '; error|Error:|\bFAIL|bad argument|not a function|refused|Unknown command' }
function Get-BenchConsolePassRx { '\bPASS\b|^(?:git-sp|UST) bench: loaded\b' }

# The lines of $Text a pattern matches (plan 31 P6: the one matcher of the parser). .NET regex, Multiline, case-
# sensitive unless -IgnoreCase; a match is reported as its whole line, each line once, in order; -First: the first.
function Find-BenchLine {
	param([string]$Text, [string]$Pattern, [switch]$IgnoreCase, [switch]$First)
	$Text = $Text -replace "`r`n", "`n"   # Multiline $ matches only before `n
	$o = [Text.RegularExpressions.RegexOptions]::Multiline
	if ($IgnoreCase) { $o = $o -bor [Text.RegularExpressions.RegexOptions]::IgnoreCase }
	$seen = @{}; $out = New-Object System.Collections.Generic.List[string]
	foreach ($m in [regex]::Matches($Text, $Pattern, $o)) {
		$s = $Text.LastIndexOf("`n", [Math]::Max(0, $m.Index - 1)) + 1
		if ($m.Index -eq 0) { $s = 0 }
		if ($seen.ContainsKey($s)) { continue }
		$seen[$s] = $true
		$e = $Text.IndexOf("`n", $m.Index); if ($e -lt 0) { $e = $Text.Length }
		$out.Add($Text.Substring($s, $e - $s).TrimEnd("`r"))
		if ($First) { break }
	}
	return $out.ToArray()   # callers wrap it in @(): an empty result is no line
}

# This step's END marker (plan 31 O1): 'BENCH-END lane=<lane> step=<step> status=PASS|FAIL|ERROR', a whole line.
# -> the status, or '' when the lines hold none for this step.
function Get-BenchEndMarker {
	param([string[]]$Lines, [string]$Step, [string]$Lane = '')
	$st = ''
	foreach ($l in $Lines) {
		if ($l -cmatch '^\s*BENCH-END\s+lane=(\S*)\s+step=(\S+)\s+status=(PASS|FAIL|ERROR)\s*$' -and $Matches[2] -ceq $Step) {
			if (-not $Lane -or -not $Matches[1] -or $Matches[1] -ceq $Lane) { $st = $Matches[3] }
		}
	}
	return $st
}

# Judge lines by a step's keys. -> checks @{ verdict = PASS|FAIL|INFO; reason }; no keys = the harness summary and
# its FAIL lines decide (as report= did before plan 31).
function Test-BenchLogText {
	param([string[]]$Lines, $Step)
	$ic = [bool]($Step -and $Step.icase)
	$all = $Lines -join "`n"
	$c = New-Object System.Collections.ArrayList
	$add = { param($v, $r) [void]$c.Add(@{ verdict = $v; reason = (ConvertTo-BenchReason $r) }) }
	foreach ($l in $Lines) { if ($l -match '^\s*LANE\s') { & $add 'INFO' $l } }
	$keyed = $Step -and (@($Step.expect).Count + @($Step.fail).Count + @($Step.counts).Count + @($Step.cases).Count)
	if (-not $keyed) {
		foreach ($l in $Lines) { if ($l -match '^\s*FAIL\s') { & $add 'FAIL' $l } }
		$sum = @($Lines | Where-Object { $_ -match (Get-BenchSummaryRx) }) | Select-Object -Last 1
		if ($sum) { & $add $(if ($sum -match '=== \S+ PASS ===') { 'PASS' } else { 'FAIL' }) $sum }
		return , $c
	}
	foreach ($re in @($Step.expect)) {
		$hit = @(Find-BenchLine -Text $all -Pattern $re -IgnoreCase:$ic -First)
		if ($hit.Count) { & $add 'PASS' "found: $($hit[0])" } else { & $add 'FAIL' "missing: /$re/" }
	}
	foreach ($re in @($Step.fail)) {
		$fl = @(Find-BenchLine -Text $all -Pattern $re -IgnoreCase:$ic)
		foreach ($l in @($fl | Select-Object -First 20)) { & $add 'FAIL' $l }
	}
	foreach ($k in @($Step.counts)) {
		$n = @(Find-BenchLine -Text $all -Pattern $k.re -IgnoreCase:$ic).Count
		$okc = if ($k.op -eq '<=') { $n -le $k.n } else { $n -ge $k.n }
		& $add $(if ($okc) { 'PASS' } else { 'FAIL' }) "count /$($k.re)/ = $n, wanted $($k.op) $($k.n)"
	}
	if (@($Step.cases).Count) {
		$crx = Get-BenchCaseRx
		$st = @(foreach ($l in $Lines) { if ($l -cmatch $crx) { @{ s = $Matches[1]; id = $Matches[2]; line = $l } } })
		$skipOk = { param($id) [bool]@($Step.allowskip | Where-Object { $id -like $_ }).Count }
		foreach ($g in @($Step.cases)) {
			$mine = @($st | Where-Object { $_.id -like $g })
			if (-not $mine.Count) {
				if (& $skipOk $g) { & $add 'INFO' "not run (allowed): $g" } else { & $add 'FAIL' "not run: $g" }
				continue
			}
			$bad = 0
			foreach ($x in $mine) {
				if ($x.s -in 'FAIL', 'ERROR') { $bad++; & $add 'FAIL' $x.line }
				elseif ($x.s -eq 'SKIP') {
					if (& $skipOk $x.id) { & $add 'INFO' "skipped (allowed): $($x.id)" }
					else { $bad++; & $add 'FAIL' "not run (SKIP): $($x.id)" }
				}
			}
			if (-not $bad) { & $add 'PASS' "cases $g`: $(@($mine | Where-Object { $_.s -eq 'PASS' }).Count) PASS" }
		}
	}
	$sum = @($Lines | Where-Object { $_ -match (Get-BenchSummaryRx) }) | Select-Object -Last 1
	if ($sum) { & $add 'INFO' $sum }
	return , $c
}

# report=<glob>[,<glob>] (ust R20261109-0809, plan 31 P4): a step is judged from the report files written since it
# opened. Complete when a file holds this step's END marker (every such file is judged), else when the newest file
# has the done line (done=/re/, default the '=== NAME PASS|FAIL ===' summary). Not complete: judged anyway, with a
# FAIL, after -WaitSec, when AutoCAD exited (-AcadGone, crash: the last 20 lines too) or on Stop (-Stopped).
# Writes <out>/<id>.report (BENCH lines, each naming its file); -> the judged files ('' = nothing new).
function Import-BenchReport {
	param([string]$RunDir, [string]$OutDir, [string]$Id, [string]$Glob, [datetime]$Since, $Step = $null,
		[string]$Lane = '', [int]$WaitSec = 0, [datetime]$Now = (Get-Date), [switch]$AcadGone, [switch]$Stopped)
	$files = @(foreach ($g in @($Glob -split ',' | Where-Object { $_ })) {
			Get-ChildItem -Path (Join-Path $RunDir ($g -replace '\\', '/')) -File -ErrorAction Ignore
		})
	$files = @($files | Where-Object { $_.LastWriteTime -ge $Since } | Sort-Object FullName -Unique)
	$files = @($files | Sort-Object LastWriteTime)
	$read = @{}
	foreach ($f in $files) { $read[$f.FullName] = @(Get-Content -LiteralPath $f.FullName -ErrorAction Ignore) }
	$ic = [bool]($Step -and $Step.icase)
	$doneRx = if ($Step -and $Step.done) { $Step.done } else { (Get-BenchSummaryRx) }
	$marked = @($files | Where-Object { Get-BenchEndMarker -Lines $read[$_.FullName] -Step $Id -Lane $Lane })
	$extra = @(); $judge = @(); $tail = $false
	$lastTxt = if ($files.Count) { $read[$files[-1].FullName] -join "`n" } else { '' }
	if ($marked.Count) { $judge = $marked }
	elseif ($files.Count -and @(Find-BenchLine -Text $lastTxt -Pattern $doneRx -IgnoreCase:$ic -First).Count) {
		$judge = @($files[-1])
	} else {
		$why = if ($AcadGone) { 'AutoCAD exited before END marker'; $tail = $true }
		elseif ($Stopped) { 'stopped before END marker' }
		elseif ($WaitSec -gt 0 -and ($Now - $Since).TotalSeconds -ge $WaitSec) { "no END marker within $WaitSec s" }
		else { '' }
		if (-not $why) { return '' }   # still running
		$extra += @{ verdict = 'FAIL'; reason = $why }
		if ($files.Count) { $judge = @($files[-1]) }
	}
	$tag = '# from ' + (($judge | ForEach-Object { "$($_.FullName) $($_.LastWriteTimeUtc.Ticks)" }) -join ' | ')
	if ($extra.Count) { $tag += " / $($extra[0].reason)" }
	$out = "$OutDir/$Id.report"
	$was = if (Test-Path -LiteralPath $out) { @(Get-Content -LiteralPath $out)[0] } else { '' }
	if ($was -eq $tag) { return '' }
	$b = @($tag)
	foreach ($e in $extra) { $b += "BENCH $Id $($e.verdict) $($e.reason)" }
	foreach ($f in $judge) {
		$p = ($f.FullName -replace '\\', '/')
		$ln = $read[$f.FullName]
		$em = Get-BenchEndMarker -Lines $ln -Step $Id -Lane $Lane
		if ($em -eq 'ERROR') { $b += "BENCH $Id FAIL the test ended on its error path (BENCH-END status=ERROR) $p" }
		foreach ($k in (Test-BenchLogText -Lines $ln -Step $Step)) { $b += "BENCH $Id $($k.verdict) $($k.reason) $p" }
		if ($tail) {
			foreach ($l in @($ln | Select-Object -Last 20)) { $b += "BENCH $Id INFO $(ConvertTo-BenchReason $l) $p" }
		}
	}
	$b += "BENCH $Id END n=$(@($b | Where-Object { $_ -match '^BENCH \S+ (PASS|FAIL) ' }).Count)"
	New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
	[IO.File]::WriteAllText($out, ($b -join "`n") + "`n")
	$names = @($judge | ForEach-Object { $_.FullName })
	return $(if ($names.Count) { $names -join ', ' } else { "(no report file: $Glob)" })
}

# The AutoCAD command line for a Start AutoCAD with no line of its own (rebuild bar, restart, an empty start-acad
# block) when .bench.ini has no [bench] acad = (ust R20261109-0651): the last start-acad block in the runbook with a
# line, else the newest acad.exe in the registry (AcadLocation), else ''.
function Find-BenchAcad {
	param($Rb, [string]$RegRoot = 'HKLM:/SOFTWARE/Autodesk/AutoCAD')
	$line = ''
	foreach ($s in @($Rb.steps)) {
		foreach ($g in @(Get-RunbookSegments -Lines @($s.body))) {
			$t = @(([string]$g.text) -split "`r?`n" | Where-Object { $_.Trim() })
			if ($g.act -eq 'start-acad' -and $t.Count) { $line = $t[0].Trim() }
		}
	}
	if ($line -or -not (Test-Path -LiteralPath $RegRoot)) { return $line }
	$keys = @(Get-ChildItem -LiteralPath $RegRoot -ErrorAction Ignore | Sort-Object PSChildName -Descending)
	foreach ($k in $keys) {
		foreach ($p in @(Get-ChildItem -LiteralPath $k.PSPath -ErrorAction Ignore)) {
			$loc = (Get-ItemProperty -LiteralPath $p.PSPath -Name AcadLocation -ErrorAction Ignore).AcadLocation
			$exe = if ($loc) { Join-Path $loc 'acad.exe' } else { '' }
			if ($exe -and (Test-Path -LiteralPath $exe)) { return "`"$exe`" /nologo" }
		}
	}
	return ''
}

# Body lines -> segments: @{ kind = 'md'; text } and @{ kind = 'code'; lang; text; run; act }.
# A fence tagged powershell / ps1 / pwsh / run gets Run; lisp / acad get Send to
# AutoCAD, open gets Open, start-acad gets Start AutoCAD (act = the lang); every fence gets Copy.
function Get-RunbookSegments {
	param([string[]]$Lines)
	$seg = @(); $buf = New-Object System.Collections.ArrayList; $lang = $null
	$runs = 'powershell', 'ps1', 'pwsh', 'run'; $acts = 'lisp', 'acad', 'open', 'start-acad'
	foreach ($l in $Lines) {
		if ($null -eq $lang -and $l -match '^\s*(```|~~~)\s*([\w+-]*)') {
			if (($buf -join '').Trim()) { $seg += @{ kind = 'md'; text = ($buf -join "`n") } }
			$buf.Clear(); $lang = $Matches[2].ToLower(); continue
		}
		if ($null -ne $lang -and $l -match '^\s*(```|~~~)\s*$') {
			$seg += @{ kind = 'code'; lang = $lang; text = ($buf -join "`n"); run = ($runs -contains $lang); act = $(if ($acts -contains $lang) { $lang } else { '' }) }
			$buf.Clear(); $lang = $null; continue
		}
		[void]$buf.Add($l)
	}
	if ($null -ne $lang) { $seg += @{ kind = 'code'; lang = $lang; text = ($buf -join "`n"); run = ($runs -contains $lang); act = $(if ($acts -contains $lang) { $lang } else { '' }) } }
	elseif (($buf -join '').Trim()) { $seg += @{ kind = 'md'; text = ($buf -join "`n") } }
	return $seg
}

# {run} {main} with backslashes, {run/} {main/} with forward slashes; no trailing slash.
function Get-BenchTokens {
	param([string]$Run, [string]$Main)
	$w = { param($p) ($p -replace '/', '\').TrimEnd('\') }
	$f = { param($p) ($p -replace '\\', '/').TrimEnd('/') }
	return @{ 'run' = (& $w $Run); 'main' = (& $w $Main); 'run/' = (& $f $Run); 'main/' = (& $f $Main) }
}

# A path in runbook text (a `code` span or a link) -> full Windows path: rooted
# paths stay, relative ones are under the run folder; quotes and spaces trimmed.
function Resolve-BenchPath {
	param([string]$Text, [string]$RunDir)
	$p = $Text.Trim().Trim('"', "'").Trim()
	if ($p -notmatch '^([A-Za-z]:[\\/]|\\\\|//)') { $p = ($RunDir.TrimEnd('\', '/') + '/' + $p.TrimStart('.', '\', '/')) }
	return ($p -replace '/', '\')
}

# True when a `code` span reads as a path (rooted, has a separator, or name.ext),
# not a command such as USTEXPORT.
function Test-BenchPathLike {
	param([string]$Text)
	$t = $Text.Trim()
	if ($t -match '\s-|[()<>|*?]') { return $false }
	return ($t -match '^([A-Za-z]:[\\/]|\\\\)' -or $t -match '^[\w.{}-]+([\\/][\w .{}-]+)+[\\/]?$' -or $t -match '^[\w-]+\.[A-Za-z]\w{0,4}$')
}

# Top-level forms of a ```lisp fence, one line each: ; and ;| |; comments
# dropped, newlines outside strings made spaces. Unbalanced text throws.
function Split-BenchLispForms {
	param([string]$Text)
	$forms = New-Object System.Collections.ArrayList; $sb = New-Object System.Text.StringBuilder
	$d = 0; $i = 0; $n = $Text.Length
	while ($i -lt $n) {
		$c = $Text[$i]
		if ($c -eq '"') {
			$j = $i + 1; while ($j -lt $n -and $Text[$j] -ne '"') { if ($Text[$j] -eq '\') { $j++ }; $j++ }
			if ($j -ge $n) { throw 'a string is not closed (missing ")' }
			if ($d -gt 0) { [void]$sb.Append($Text.Substring($i, $j - $i + 1)) }
			$i = $j + 1; continue
		}
		if ($c -eq ';') {
			if ($i + 1 -lt $n -and $Text[$i + 1] -eq '|') { $e = $Text.IndexOf('|;', $i + 2); $i = if ($e -lt 0) { $n } else { $e + 2 } }
			else { while ($i -lt $n -and $Text[$i] -ne "`n") { $i++ } }
			if ($d -gt 0) { [void]$sb.Append(' ') }
			continue
		}
		if ($c -eq '(') { $d++ }
		if ($d -gt 0) { [void]$sb.Append($(if ($c -eq "`r" -or $c -eq "`n" -or $c -eq "`t") { ' ' } else { $c })) }
		if ($c -eq ')') {
			$d--
			if ($d -lt 0) { throw "an extra ')' at character $i" }
			if ($d -eq 0) { [void]$forms.Add(($sb.ToString() -replace ' {2,}', ' ')); [void]$sb.Clear() }
		}
		$i++
	}
	if ($d -gt 0) { throw "$d '(' not closed" }
	return [string[]]$forms
}

# '"C:\a b\acad.exe" /p x' -> @{ exe; args }; an unquoted first word is the exe.
function Split-BenchCommandLine {
	param([string]$Text)
	$t = $Text.Trim()
	if ($t -match '^"([^"]+)"\s*(.*)$') { return @{ exe = $Matches[1]; args = $Matches[2] } }
	if ($t -match '^(\S+)\s*(.*)$') { return @{ exe = $Matches[1]; args = $Matches[2] } }
	return @{ exe = ''; args = '' }
}

# Action fences (ust research 24 F4): the PowerShell script the Run machinery
# starts for ```lisp / ```acad (Send to AutoCAD), ```open and ```start-acad.
# The script runs in powershell.exe 5.1 (COM GetActiveObject), prints what it
# did, and exits 0 or 1. $global:BenchAcadStub / $global:BenchOpenStub stand in
# for AutoCAD and the shell in tests.
# Auto steps (plan 30 S12, ust review H1, M6): -IdleSec is the wait between forms; -Clear is a file deleted once
# AutoCAD is idle (refused when it stays); -Begin is a form sent first (the run's begin marker).
function ConvertTo-BenchActionScript {
	param([string]$Kind, [string]$Text, [string]$RunDir, [string]$Acad = '', [string]$Main = '', [int]$IdleSec = 120,
		[string]$Clear = '', [string]$Begin = '', [string]$StepId = '', [string]$LaneId = '')
	$rf = Get-BenchRebuildState -RunDir $RunDir
	# start-acad and the restart jobs (ust review N6) touch no run code: rebuild-first needs them
	if ($rf -and $Kind -notin 'start-acad', 'acad-unsaved', 'acad-quit') { throw "Refused: $($rf.reason)" }
	$q = { param($s) "'" + ([string]$s).Replace("'", "''") + "'" }
	$list = { param($a) '@(' + ((@($a) | ForEach-Object { & $q $_ }) -join ', ') + ')' }
	$pre = @'
$ErrorActionPreference = 'Stop'
function Get-Acad { if ($global:BenchAcadStub) { return $global:BenchAcadStub }; foreach ($p in 'AutoCAD.Application.24.3', 'AutoCAD.Application') { try { return [Runtime.InteropServices.Marshal]::GetActiveObject($p) } catch { } }; return $null }
function Invoke-Acad([scriptblock]$Call) {
	for ($i = 0; $i -lt 40; $i++) {
		try { return (& $Call) } catch {
			$e = $_.Exception; $busy = $false
			while ($e) { if ($e.HResult -eq -2147418111 -or $e.HResult -eq -2147417846) { $busy = $true }; $e = $e.InnerException }   # RPC_E_CALL_REJECTED, RPC_E_SERVERCALL_RETRYLATER
			if (-not $busy) { throw }
			Start-Sleep -Milliseconds 250
		}
	}
	throw 'AutoCAD stayed busy for 10 s (a dialog or a command is open?). Finish it in AutoCAD, then press the button again.'
}
function Get-AcadPrompt($A) { try { [string]$A.ActiveDocument.GetVariable('LASTPROMPT') } catch { '?' } }
function Wait-AcadIdle($A, [int]$Sec = 120) {
	$t = Get-Date
	while (-not (Invoke-Acad { $A.GetAcadState().IsQuiescent })) {
		if (((Get-Date) - $t).TotalSeconds -gt $Sec) { throw "AutoCAD is not idle after $Sec s; it waits at: $(Get-AcadPrompt $A). Answer or press Esc in AutoCAD, then try again." }
		Start-Sleep -Milliseconds 200
	}
}
function Connect-Acad {
	$n = @(Get-Process acad -ErrorAction SilentlyContinue).Count
	if ($n -gt 1 -and -not $global:BenchAcadStub) { throw "$n AutoCAD sessions are running; close all but one (the bench cannot tell which one to use)." }
	$a = Get-Acad
	if (-not $a) { throw 'AutoCAD is not running (or not ready yet): start it first.' }
	Wait-AcadIdle $a 30
	return $a
}

'@
	switch -Regex ($Kind) {
		'^(lisp|acad)$' {
			if ($Kind -eq 'lisp') { $items = Split-BenchLispForms $Text; $end = "' '" }
			else { $items = @($Text -split "`r?`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -and -not $_.StartsWith(';') }); $end = '[string][char]13' }
			if (-not @($items).Count) { throw "the $Kind block has nothing to send" }
			# plan 31 P3: the test code learns its runbook step and lane (gsb:step, gsb:lane) before anything else
			if ($StepId -match '^[\w.-]+$' -and $LaneId -match '^[\w.-]*$') {
				$items = @("(setq gsb:step `"$StepId`" gsb:lane `"$LaneId`")") + @($items)
			}
			$clr = if ($Clear) { & $q $Clear } else { "''" }
			$beg = if ($Begin) { & $q $Begin } else { "''" }
			return $pre + @"
`$items = $(& $list $items); `$end = $end; `$clr = $clr; `$beg = $beg; `$idle = $IdleSec
try {
	`$a = Connect-Acad
	# owner 2026-11-09: a drawing with no units (INSUNITS 0) gets meters (6) before anything is sent
	`$u = try { [int](Invoke-Acad { `$a.ActiveDocument.GetVariable('INSUNITS') }) } catch { -1 }
	if (`$u -eq 0) {
		Invoke-Acad { `$a.ActiveDocument.SetVariable('INSUNITS', [int16]6) } | Out-Null
		Write-Output 'INSUNITS was 0 (unitless): set to 6 (meters)'
	}
	if (`$clr) {   # the old result goes only once AutoCAD is idle: an earlier form can no longer write to it
		Remove-Item -LiteralPath `$clr -Force -ErrorAction SilentlyContinue
		if (Test-Path -LiteralPath `$clr) { Write-Output "FAILED: cannot delete `$clr"; exit 1 }
		# ust review C1: this run's begin marker goes straight into the result file, never through an AutoCAD echo
		if (`$beg) { [IO.File]::WriteAllText(`$clr, "`$beg``r``n") }
	}
	for (`$k = 0; `$k -lt `$items.Count; `$k++) {
		# the next one only when the last has finished; the last may wait at a prompt for the tester
		if (`$k) { Wait-AcadIdle `$a `$idle }
		Write-Output "send: `$(`$items[`$k])"
		Invoke-Acad { `$a.ActiveDocument.SendCommand(`$items[`$k] + `$end) } | Out-Null
	}
	Write-Output "AutoCAD: `$(Get-AcadPrompt `$a)"
	exit 0
} catch { Write-Output "FAILED: `$(`$_.Exception.Message)"; exit 1 }
"@
		}
		'^open$' {
			$items = @($Text -split "`r?`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ -and -not $_.StartsWith('#') } | ForEach-Object { Resolve-BenchPath $_ $RunDir })
			if (-not $items.Count) { throw 'the open block has no path' }
			return $pre + @"
`$items = $(& $list $items); `$code = 0; `$a = `$null
foreach (`$p in `$items) {
	if (-not (Test-Path -LiteralPath `$p)) { Write-Output "not found: `$p"; `$code = 1; continue }
	if (`$p -match '\.(dwg|dxf)$') {
		try {
			if (-not `$a) { `$a = Connect-Acad }
			`$ds = `$a.Documents; `$hit = `$null
			for (`$i = 0; `$i -lt `$ds.Count; `$i++) { `$x = Invoke-Acad { `$ds.Item(`$i) }; if ([string]`$x.FullName -ieq `$p) { `$hit = `$x } }
			if (`$hit) { Invoke-Acad { `$hit.Activate() } | Out-Null; Write-Output "made active in AutoCAD: `$p" }
			else { Invoke-Acad { `$ds.Open(`$p, `$false) } | Out-Null; Write-Output "opened in AutoCAD: `$p" }
		} catch { Write-Output "FAILED to open in AutoCAD: `$p - `$(`$_.Exception.Message)"; `$code = 1 }
	} else {
		if (`$global:BenchOpenStub) { & `$global:BenchOpenStub `$p } else { Invoke-Item -LiteralPath `$p }
		Write-Output "opened: `$p"
	}
}
exit `$code
"@
		}
		'^start-acad$' {
			$line = if ($Text.Trim()) { ($Text -split "`r?`n" | Where-Object { $_.Trim() } | Select-Object -First 1) } else { $Acad }
			if (-not ([string]$line).Trim()) {
				throw ('no AutoCAD command line: none in the block, no [bench] acad = in .bench.ini on origin/main, no ' +
					'start-acad block in the runbook, no AutoCAD in the registry. Set [bench] acad = ' +
					'"C:\Program Files\Autodesk\AutoCAD 2024\acad.exe" /nologo, push it to main, then git-sp -Bench pull')
			}
			$c = Split-BenchCommandLine $line
			$st = (Resolve-BenchPath 'bench-run/acad-status.txt' $RunDir)
			$leaf = if ($Main) { Split-Path -Leaf ($Main -replace '\\', '/') } else { '' }
			return $pre + @"
`$exe = $(& $q $c.exe); `$arg = $(& $q $c.args); `$st = $(& $q $st)
`$run = @(Get-Process acad -ErrorAction SilentlyContinue)
if (`$run.Count) { Write-Output "AutoCAD is already running (PID `$((`$run | ForEach-Object { `$_.Id }) -join ', ')). Close it first when this step needs a fresh start."; exit 1 }
if (-not (Test-Path -LiteralPath `$exe)) { Write-Output "not found: `$exe (set [bench] acad = in .bench.ini, or put the command line in the block)"; exit 1 }
`$t0 = Get-Date
Write-Output "start: `"`$exe`" `$arg"
`$sp = @{ FilePath = `$exe; WorkingDirectory = $(& $q ($RunDir -replace '/', '\')) }; if (`$arg) { `$sp.ArgumentList = `$arg }
# per-process only (this script's own environment, inherited by the child): the bundle LISP loads the run only in THIS AutoCAD
`$env:GSB_BENCH_RUN = $(& $q ($RunDir -replace '/', '\')); `$env:GSB_BENCH_REPO = $(& $q $leaf)
# plan 30 V3: a nonce per AutoCAD start; the bundle writes it into acad-status.txt, so an old status cannot pass
`$env:GSB_BENCH_NONCE = [guid]::NewGuid().ToString('N').Substring(0, 12)
`$nf = $(& $q (Resolve-BenchPath 'bench-run/acad-nonce.txt' $RunDir))
[IO.File]::WriteAllLines(`$nf, [string[]]@(`$env:GSB_BENCH_NONCE, `$t0.ToString('o')))
Start-Process @sp
for (`$i = 0; `$i -lt 360; `$i++) {
	if ((Test-Path -LiteralPath `$st) -and (Get-Item -LiteralPath `$st).LastWriteTime -gt `$t0) { Write-Output "bench bundle loaded:"; Get-Content -LiteralPath `$st; exit 0 }
	Start-Sleep -Milliseconds 500
}
Write-Output "FAILED: AutoCAD did not report through the bench bundle in 3 min (`$st unchanged). Is the bench bundle installed (git-sp -Bench pull)?"
# ust R20261109-1033: what the bundle saw (its own log, the run line it picks from), so the cause is in the step log
`$bd = "`$env:APPDATA\Autodesk\ApplicationPlugins\git-sp-bench.bundle"
foreach (`$f in "`$bd\PackageContents.xml", "`$bd\Contents\git-sp-bench.lsp", "`$bd\Contents\runs\$leaf.txt") {
	Write-Output "`$(if (Test-Path -LiteralPath `$f) { 'found' } else { 'MISSING' }): `$f"
}
`$rl = "`$bd\Contents\runs\$leaf.txt"
if (Test-Path -LiteralPath `$rl) { Write-Output "run line: `$(Get-Content -Raw -LiteralPath `$rl)" }
`$bl = "`$bd\Contents\logs\bench-trace-bundle.log"
if (Test-Path -LiteralPath `$bl) { Write-Output "last lines of `$(`$bl):"; Get-Content -LiteralPath `$bl -Tail 25 }
else {
	Write-Output "no bundle log `$(`$bl): AutoCAD did not load the bundle (SECURELOAD, trust, or the bundle folder)"
}
exit 1
"@
		}
		# plan 30 S8 (ust review round 4 #4): read in the action process, not the window
		'^acad-unsaved$' {
			return $pre + @"
try {
	`$a = Get-Acad
	if (-not `$a) { Write-Output 'FAILED: AutoCAD is not reachable through COM'; exit 1 }
	foreach (`$d in @(`$a.Documents)) { if (-not `$d.Saved) { Write-Output "unsaved: `$(`$d.Name)" } }
	Write-Output 'listed'; exit 0
} catch { Write-Output "FAILED: `$(`$_.Exception.Message)"; exit 1 }
"@
		}
		# $Text: the hwnd from acad-status.txt; refuses another or a second AutoCAD (ust review #8)
		'^acad-quit$' {
			return $pre + @"
`$want = $(& $q $Text)
try {
	`$p = @(Get-Process acad -ErrorAction SilentlyContinue)
	if (`$null -ne `$global:BenchAcadProcs) { `$p = @(`$global:BenchAcadProcs) }   # tests: stand-in processes
	if (`$p.Count -ne 1) { Write-Output "FAILED: `$(`$p.Count) AutoCAD processes run; close the others first"; exit 1 }
	if (`$want -and [string][long]`$p[0].MainWindowHandle -ne `$want) {
		Write-Output 'FAILED: the running AutoCAD is not the bench one'; exit 1
	}
	`$a = Get-Acad
	if (-not `$a) { Write-Output 'FAILED: AutoCAD is not reachable through COM'; exit 1 }
	foreach (`$d in @(`$a.Documents)) { [void]`$d.Close(`$false) }
	`$a.Quit()
	if (`$p.Count -and -not `$p[0].WaitForExit(60000)) { Write-Output 'FAILED: acad.exe still runs after 60 s'; exit 1 }
	Write-Output 'quit'; exit 0
} catch { Write-Output "FAILED: `$(`$_.Exception.Message)"; exit 1 }
"@
		}
		default { throw "no action for a ``$Kind block" }
	}
}

# Restart after a refusal (plan 30 S8, owner D1: a refused VLX stays loaded, ltm 2357): the confirm text from the
# acad-unsaved job's log. -> @{ ok; why; ask }
function Get-BenchRestartAsk {
	param([string[]]$Lines, [string]$Code)
	if ($Code -ne '0' -or -not ($Lines -contains 'listed')) {
		$f = @($Lines | Where-Object { $_ -like 'FAILED:*' })
		return @{ ok = $false; why = $(if ($f.Count) { $f[-1] } else { "exit $Code" }); ask = '' }
	}
	$un = @($Lines | Where-Object { $_ -like 'unsaved: *' } | ForEach-Object { $_.Substring(9) })
	$m = 'Quit AutoCAD and start it again for this run?'
	if ($un.Count) { $m += "`n`nThese drawings have UNSAVED changes, which are lost:`n  " + ($un -join "`n  ") }
	return @{ ok = $true; why = ''; ask = $m }
}

# AutoCAD command-line lines that read as errors (ust 24: shown under the note, in the review, in RESULT.tsv).
function Get-BenchErrorLines {
	param([string]$Text)
	$rx = Get-BenchErrorRx
	return @(($Text -split "`r?`n") | Where-Object { $_ -cmatch $rx } | ForEach-Object { $_.Trim() })
}

# Console text for people (owner 2026-11-06): the raw logs stay as they are (evidence, expect
# checks); the Output pane shows this. A ';' path list goes one path per line, numbered; an
# empty "Command:" prompt run collapses; a repeated line shows once with (xN); FAIL / error
# lines get "!!", PASS / loaded lines "ok"; -Summary puts the counts on top. Hidden (ust 2026-11-06):
# AutoCAD start-up noise, MAKELISPAPP symbol dumps, the Send fence's "send:" echo; a multi-line
# "> " echo shows its first line only; doubled backslashes in a path list are single.
function Format-BenchConsole {
	param([string]$Text, [switch]$Summary)
	if (-not $Text) { return '' }
	$out = New-Object System.Collections.Generic.List[string]
	$nf = 0; $np = 0; $prev = $null; $rep = 0; $hid = 0; $echo = $false
	$badRx = Get-BenchConsoleFailRx; $okRx = Get-BenchConsolePassRx
	$noise = @('^\s*(?:Regenerating model\.|AutoCAD menu utilities loaded\..*|\*Cancel\*|_RIBBON|send: .*)\s*$',
		'\(COMMAND "_NETLOAD"', '^\s*;;[A-Z]+:') -join '|'
	$flush = {
		if ($null -eq $prev) { return }
		if ($rep -gt 1) { $out[$out.Count - 1] = $out[$out.Count - 1] + "   (x$rep)" }
	}
	foreach ($raw in ($Text -split "`r?`n")) {
		$l = $raw.TrimEnd()
		if ($l -match $noise) { $hid++; continue }
		if ($l.StartsWith('> ')) {
			if ($echo) { $hid++; continue }
			$echo = $true; $out.Add($l); continue
		}
		$echo = $false
		if ($l -match '^\s*Command:\s*$' -and $out.Count -and $out[$out.Count - 1] -match '^\s*Command:\s*$') { continue }
		if ($l -eq $prev) {
			$rep++
			if ($out[$out.Count - 1] -like '!! *') { $nf++ } elseif ($out[$out.Count - 1] -like 'ok *') { $np++ }
			continue
		}
		& $flush; $prev = $l; $rep = 1
		if ($l -match '^\s*Command:\s*$') { $out.Add($l); continue }
		$l = $l -replace '^(Command:\s*)(?:Command:\s*)+', '$1'
		$segs = @(($l -replace '\\\\', '\') -split ';')
		$paths = @($segs | Where-Object { $_ -match '^\s*(?:[A-Za-z]:[\\/]|\\\\|%\w+%|\.{0,2}[\\/])' })
		if ($segs.Count -ge 3 -and $paths.Count -ge 2) {
			$head = ''; $first = $segs[0]
			$lead = '^(.*?[=:]\s*)((?:[A-Za-z]:[\\/]|\\\\|%\w+%).*)$'   # 'NAME=' before the first path
			if ($first -match $lead) { $head = $Matches[1].TrimEnd(); $segs[0] = $Matches[2] }
			$head = $head.TrimEnd('=', ':', ' ')
			$out.Add($(if ($head) { "$head ($($segs.Count) paths):" } else { "($($segs.Count) paths):" }))
			$i = 0
			foreach ($g in $segs) { $i++; $out.Add(('    {0,2}  {1}' -f $i, $g.Trim())) }
			continue
		}
		if ($l -cmatch $badRx) { $nf++; $out.Add("!! $l"); continue }
		if ($l -cmatch $okRx) { $np++; $out.Add("ok $l"); continue }
		if ($l -match '^\s*Command:\s*\S' -and $out.Count -and $out[$out.Count - 1] -ne '') { $out.Add('') }
		$out.Add($l)
	}
	& $flush
	$bl = @($out | Where-Object { $_ -match '^(?:!! |ok )?BENCH ' })   # plan 30 S6: verdict lines first
	if ($bl.Count) { $out = @($bl) + '' + @($out | Where-Object { $_ -notmatch '^(?:!! |ok )?BENCH ' }) }
	$body = ($out -join "`r`n").TrimEnd()
	if ($Summary -and ($nf + $np + $hid)) {
		$body = "== $nf FAIL/error line(s), $np PASS/loaded line(s), $hid noise line(s) hidden ==`r`n" + $body
	}
	return $body
}

# Build stamp of a VLX without loading it (ust 24 F9). Strings inside a VLX are
# encrypted; the plain LOAD record near the start lists the member names, and the
# repo adds a member named <prefix>stamp_<build, - as _>. -> @{ state = ok | bad |
# none | missing; text }.
function Test-BenchVlxStamp {
	param([string]$Path, [string]$Expected)
	$leaf = [IO.Path]::GetFullPath($Path)
	if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return @{ state = 'missing'; text = "${leaf}: not built" } }
	$fs = [IO.File]::OpenRead($Path)
	try { $buf = New-Object byte[] ([Math]::Min($fs.Length, 65536)); $got = $fs.Read($buf, 0, $buf.Length) } finally { $fs.Dispose() }
	$s = [Text.Encoding]::GetEncoding(28591).GetString($buf, 0, $got)
	$m = [regex]::Match($s, '\(:fas "[A-Za-z0-9_]*?stamp_([^"]+)"\)')
	if (-not $m.Success) { return @{ state = 'none'; text = "${leaf}: no stamp (built before stamping)" } }
	$b = $m.Groups[1].Value
	if ($Expected -and ($b -ieq ($Expected.Trim() -replace '-', '_'))) { return @{ state = 'ok'; text = "${leaf}: $($Expected.Trim())" } }
	return @{ state = 'bad'; text = "${leaf}: build $($b -replace '_', '-'), expected $(if ($Expected) { $Expected.Trim() } else { '?' })" }
}

# Repo hook <main>/tools/bench-finish.ps1 -RunFolder -RunId -Main, run when Finish is
# pressed (e.g. put settings back). Output in bench-run/finish.log. -> @{ code; last } or $null.
function Invoke-BenchFinishHook {
	param([string]$Main, [string]$RunDir, [string]$RunId, [string]$Exe = 'powershell.exe')
	$hs = "$Main/tools/bench-finish.ps1"
	if (-not $Main -or -not (Test-Path -LiteralPath $hs)) { return $null }
	New-Item -ItemType Directory -Force -Path "$RunDir/bench-run" | Out-Null
	$o = @(& $Exe -NoProfile -ExecutionPolicy Bypass -File $hs -RunFolder $RunDir -RunId $RunId -Main $Main 2>&1 | ForEach-Object { "$_" })
	$code = $LASTEXITCODE
	$o += "bench-finish: exit $code $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
	[IO.File]::WriteAllLines("$RunDir/bench-run/finish.log", [string[]]$o)
	return @{ code = $code; last = @($o | Where-Object { $_ -match '\S' } | Select-Object -Last 2) -join '  |  ' }
}

# True when every task of a step is done (`[x]`) in the ledger text (30-TODO + 35-DONE).
function Test-BenchTaskSettled {
	param([string]$Ledger, [string]$Task)
	$ids = @($Task -split '[\s,;]+' | Where-Object { $_ })
	if (-not $ids.Count -or -not $Ledger) { return $false }
	foreach ($t in $ids) { if ($Ledger -notmatch ('`\[x\]`\s+' + [regex]::Escape($t) + '(?![\w.])')) { return $false } }
	return $true
}

function Read-Runbook {
	param([string]$Path, [hashtable]$Tokens = @{})
	$groups = @(); $steps = @(); $cur = $null; $fence = $false; $g = ''; $fresh = $false
	$text = [IO.File]::ReadAllText($Path)
	foreach ($k in $Tokens.Keys) { $text = $text.Replace('{' + $k + '}', [string]$Tokens[$k]) }   # {run} / {main}: shown expanded; the filled runbook keeps the tokens
	foreach ($line in ($text -split "`r?`n")) {
		# `**Required state:** text` under a lane or step heading: shown as a banner, keeps the heading fresh for its marker
		if (-not $fence -and $cur -and $line -match '^\*\*Required state:\*\*\s*(.*?)\s*$') { $cur.state = $Matches[1]; continue }
		$was = $fresh; $fresh = $fresh -and -not $line.Trim()   # blank lines keep a heading "fresh"
		if ($line -match '^\s*(```|~~~)') { $fence = -not $fence }
		if (-not $fence -and $line -match (Get-BenchStepHead)) {
			$sid = if ($Matches[2]) { $Matches[2] } else { $Matches[3] }
			$cur = [pscustomobject]@{ id = $sid; title = $Matches[4]; group = $g; task = ''; push = ''; state = ''; type = 'manual'; timeout = 0; expect = @(); fail = @(); collect = @(); restart = ''; mode = ''; since = ''; report = ''; done = ''; counts = @(); cases = @(); allowskip = @(); wait = 0; icase = $false; settled = $false; hidden = $false; body = (New-Object System.Collections.ArrayList) }
			$fresh = ($Matches[1].Length -in 2, 3)   # a lane heading takes a marker too (mode=, ust 2026-11-09)
			if ($Matches[1].Length -eq 2) { $g = $cur.id; $cur.group = ''; $groups += $cur } else { $steps += $cur }
			continue
		}
		if (-not $fence -and $line -match '^#{1,3}\s') { $cur = $null; continue }
		if (-not $cur) { continue }
		if ($line -match '<!--\s*step:\s*(.*?)\s*-->') {
			$meta = $Matches[1]
			if (-not $was) { continue }   # a marker not directly under a step heading belongs to no step (check_runbook reports it)
			if ($meta -match 'task=([\w.,]+)') { $cur.task = $Matches[1].TrimEnd(',') }
			if ($meta -match 'push=(\S+)') { $cur.push = $Matches[1] }
			Set-RunbookStepKeys -Step $cur -Meta $meta
			continue
		}
		if ($line -match '^\*\*Result:\*\*') { continue }
		[void]$cur.body.Add($line)
	}
	return @{ groups = $groups; steps = $steps }
}

function ConvertTo-HtmlText {
	param([string]$s)
	return $s.Replace('&', '&amp;').Replace('<', '&lt;').Replace('>', '&gt;').Replace('"', '&quot;')
}

# Inline markdown on a text line: `code`, **bold**, *italic*, [text](url).
# Everything is HTML-escaped first; only http(s) and relative links survive.
function ConvertTo-HtmlInline {
	param([string]$s)
	$parts = $s -split '`'
	if ($parts.Count % 2 -eq 0) { $parts = @($s) }   # unbalanced backtick: no code spans
	$out = ''
	for ($i = 0; $i -lt $parts.Count; $i++) {
		$t = ConvertTo-HtmlText $parts[$i]
		if ($parts.Count -gt 1 -and $i % 2 -eq 1) { $out += "<code>$t</code>"; continue }
		$t = $t -replace '\*\*(.+?)\*\*', '<b>$1</b>'
		$t = $t -replace '(?<![\*\w])\*(?![\s\*])(.+?)(?<![\s\*])\*(?!\*)', '<i>$1</i>'
		$t = $t -replace '\[([^\]]+)\]\((https?://[^)\s]+|[\w./#][^):\s]*)\)', '<a href="$2">$1</a>'
		$out += $t
	}
	return $out
}

function ConvertTo-BasicHtml {
	param([string]$Markdown)
	$o = New-Object System.Text.StringBuilder
	$lines = @($Markdown -split "`r?`n")
	$mode = ''   # '' | p | ul | ol | code | table
	$close = { if ($mode -in 'p', 'ul', 'ol') { [void]$o.Append("</$mode>`n") }; if ($mode -eq 'table') { [void]$o.Append("</table>`n") }; Set-Variable mode '' -Scope 1 }
	for ($i = 0; $i -lt $lines.Count; $i++) {
		$l = $lines[$i]
		if ($mode -eq 'code') {
			if ($l -match '^\s*(```|~~~)') { [void]$o.Append("</pre>`n"); $mode = '' } else { [void]$o.Append((ConvertTo-HtmlText $l) + "`n") }
			continue
		}
		if ($l -match '^\s*<!--.*-->\s*$') { continue }
		if ($l -match '^\s*(```|~~~)') { & $close; [void]$o.Append('<pre>'); $mode = 'code'; continue }
		if ($l -match '^\s*$') { & $close; continue }
		if ($l -match '^(#{1,6})\s+(.*)$') { & $close; $n = $Matches[1].Length; [void]$o.Append("<h$n>" + (ConvertTo-HtmlInline $Matches[2]) + "</h$n>`n"); continue }
		if ($l -match '^\s*\|') {
			if ($mode -ne 'table') { & $close; [void]$o.Append("<table border=1 cellpadding=3 cellspacing=0>`n"); $mode = 'table'; $head = ($i + 1 -lt $lines.Count -and $lines[$i + 1] -match '^\s*\|?[\s:|-]+\|[\s:|-]*$' -and $lines[$i + 1] -match '-') }
			if ($l -match '^\s*\|?[\s:|-]+\|[\s:|-]*$' -and $l -match '-') { continue }
			$tag = if ($head) { 'th' } else { 'td' }; $head = $false
			$cells = ($l.Trim() -replace '^\||\|$', '') -split '\|'
			[void]$o.Append('<tr>' + (($cells | ForEach-Object { "<$tag>" + (ConvertTo-HtmlInline $_.Trim()) + "</$tag>" }) -join '') + "</tr>`n")
			continue
		}
		if ($l -match '^\s*[-*+]\s+(.*)$') { if ($mode -ne 'ul') { & $close; [void]$o.Append("<ul>`n"); $mode = 'ul' }; [void]$o.Append('<li>' + (ConvertTo-HtmlInline $Matches[1]) + "</li>`n"); continue }
		if ($l -match '^\s*\d+[.)]\s+(.*)$') { if ($mode -ne 'ol') { & $close; [void]$o.Append("<ol>`n"); $mode = 'ol' }; [void]$o.Append('<li>' + (ConvertTo-HtmlInline $Matches[1]) + "</li>`n"); continue }
		if ($mode -ne 'p') { & $close; [void]$o.Append("<p>"); $mode = 'p' } else { [void]$o.Append(' ') }
		[void]$o.Append((ConvertTo-HtmlInline $l.Trim()))
	}
	if ($mode -eq 'code') { [void]$o.Append("</pre>`n") } else { & $close }
	return $o.ToString()
}

# results.json: { steps: [{id, result, note, files[]}], general, abort }.
# State = @{ answers = ordered id -> @{result; note; files}; general; abort }.
function New-RunState { return @{ answers = [ordered]@{}; general = ''; abort = '' } }

function Save-RunState {
	param([string]$Path, $State)
	$steps = @()
	foreach ($k in $State.answers.Keys) {
		$a = $State.answers[$k]
		$steps += [pscustomobject]@{
			id = $k; result = [string]$a.result; note = [string]$a.note; files = @($a.files)
			acaderr = @($a.acaderr | Where-Object { $_ }); at = (ConvertTo-BenchIsoText $a.at)
			benchwhy = [string]$a.benchwhy; judge = [string]$a.judge; pending = (ConvertTo-BenchIsoText $a.pending)
		}
	}
	$j = ConvertTo-Json -InputObject ([pscustomobject]@{ steps = $steps; general = [string]$State.general; abort = [string]$State.abort }) -Depth 5
	[IO.File]::WriteAllText($Path, $j, (New-Object System.Text.UTF8Encoding $false))
}

function Import-RunState {
	param([string]$Path)
	$st = New-RunState
	if (-not (Test-Path -LiteralPath $Path)) { return $st }
	$j = [IO.File]::ReadAllText($Path) | ConvertFrom-Json
	foreach ($s in @($j.steps)) {
		if (-not $s.id) { continue }
		$st.answers[[string]$s.id] = @{
			result = [string]$s.result; note = [string]$s.note; files = @($s.files | Where-Object { $_ })
			# ust review N4: pwsh 7 reads ISO times as DateTime
			acaderr = @($s.acaderr | Where-Object { $_ }); at = (ConvertTo-BenchIsoText $s.at)
			benchwhy = [string]$s.benchwhy; judge = [string]$s.judge; pending = (ConvertTo-BenchIsoText $s.pending)
		}
	}
	$st.general = [string]$j.general; $st.abort = [string]$j.abort
	return $st
}

# RESULT.tsv rows (pass | fail | blocked | na) for Write-BenchResult. A step
# without task= takes $DefaultTask; an aborted run adds one blocked row.
function Get-RunbookRows {
	param($Steps, $State, [string]$DefaultTask = '')
	$rows = @()
	foreach ($s in $Steps) {
		$a = $State.answers[$s.id]
		if (-not $a -or -not $a.result) { continue }
		$t = if ($s.task) { $s.task } else { $DefaultTask }
		foreach ($one in @($t -split '[\s,;]+' | Where-Object { $_ })) {   # task=T1,T2: one row per task
			$note = [string]$a.note
			if (@($a.acaderr).Count) { $note = ($note.TrimEnd() + "`n[AutoCAD $(@($a.acaderr).Count) error line(s): " + ((@($a.acaderr) | Select-Object -First 5) -join ' | ') + ']').TrimStart() }
			if (@($a.files).Count) { $note = ($note.TrimEnd() + "`n[files: " + (@($a.files) -join ', ') + ']').TrimStart() }
			$rows += [pscustomobject]@{ step = $s.id; task = $one; result = $a.result; note = $note }
		}
	}
	if ($State.abort) { $rows += [pscustomobject]@{ step = 'abort'; task = $DefaultTask; result = 'blocked'; note = "run aborted: $($State.abort)" } }
	return $rows
}

# The runbook with every answered step's `**Result:**` line filled in.
function Write-FilledRunbook {
	param([string]$Path, [string]$Out, $State)
	$raw = [IO.File]::ReadAllText($Path)
	$nl = if ($raw.Contains("`r`n")) { "`r`n" } else { "`n" }
	$label = @{ pass = 'PASS'; fail = 'FAIL'; blocked = 'BLOCKED'; na = 'N/A' }
	$res = New-Object System.Collections.ArrayList
	$cur = $null; $fence = $false; $done = @{}
	foreach ($line in ($raw -split "`r?`n")) {
		if ($line -match '^\s*(```|~~~)') { $fence = -not $fence }
		if (-not $fence -and $line -match (Get-BenchStepHead)) { $cur = if ($Matches[1].Length -eq 3) { if ($Matches[2]) { $Matches[2] } else { $Matches[3] } } else { $null } }
		elseif (-not $fence -and $line -match '^#{1,3}\s') { $cur = $null }
		if ($cur -and -not $done[$cur] -and $line -match '^\*\*Result:\*\*' -and $State.answers[$cur] -and $State.answers[$cur].result) {
			$a = $State.answers[$cur]; $done[$cur] = $true
			$line = "**Result:** $($label[$a.result])"
			if ($a.note) { $line += ' - ' + (([string]$a.note) -replace '\s+', ' ') }
			if (@($a.files).Count) { $line += ' (files: ' + (@($a.files) -join ', ') + ')' }
		}
		[void]$res.Add($line)
	}
	$txt = $res -join $nl
	if ($State.general) { $txt = $txt.TrimEnd() + "$nl$nl## General comments$nl$nl$($State.general)$nl" }
	[IO.File]::WriteAllText($Out, $txt, (New-Object System.Text.UTF8Encoding $false))
}

# Finish step shared by the window and tests: RESULT.tsv + filled runbook into
# <run folder>/bench-run; -Bench push picks both up from there.
function Complete-BenchRunbook {
	param([string]$Runbook, [string]$OutDir, $Steps, $State, [string]$DefaultTask = '', [string[]]$Files = @())
	New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
	Write-BenchResult -Path "$OutDir/RESULT.tsv" -Rows (Get-RunbookRows -Steps $Steps -State $State -DefaultTask $DefaultTask) -Files $Files
	Write-FilledRunbook -Path $Runbook -Out "$OutDir/$([IO.Path]::GetFileName($Runbook))" -State $State
}

function Test-BenchWindowHost {
	return [bool]($IsWindows -or $PSVersionTable.PSEdition -eq 'Desktop')
}

# --- Plan 20: pure helpers the WPF window uses (Linux-tested) ----------------

# Markdown text -> blocks: @{k='h';n;t} @{k='p';t} @{k='ul'|'ol';items} @{k='table';rows;head}.
function Get-MdBlocks {
	param([string]$Text)
	$out = New-Object System.Collections.ArrayList
	$para = New-Object System.Collections.ArrayList; $list = $null; $tbl = $null
	$flush = {
		if ($para.Count) { [void]$out.Add(@{ k = 'p'; t = ($para -join ' ') }); $para.Clear() }
		if ($list) { [void]$out.Add($list); Set-Variable list $null -Scope 1 }
		if ($tbl) { [void]$out.Add($tbl); Set-Variable tbl $null -Scope 1 }
	}
	foreach ($l in @($Text -split "`r?`n")) {
		if ($l -match '^\s*<!--.*-->\s*$') { continue }
		if ($l -match '^\s*$') { & $flush; continue }
		if ($l -match '^(#{1,6})\s+(.*)$') { & $flush; [void]$out.Add(@{ k = 'h'; n = $Matches[1].Length; t = $Matches[2] }); continue }
		if ($l -match '^\s*\|') {
			if (-not $tbl) { & $flush; $tbl = @{ k = 'table'; rows = (New-Object System.Collections.ArrayList); head = $false } }
			if ($l -match '^\s*\|?[\s:|-]+\|[\s:|-]*$' -and $l -match '-') { if ($tbl.rows.Count -eq 1) { $tbl.head = $true }; continue }
			[void]$tbl.rows.Add(@((($l.Trim() -replace '^\||\|$', '') -split '\|') | ForEach-Object { $_.Trim() })); continue
		}
		$kind = if ($l -match '^\s*[-*+]\s+(.*)$') { 'ul' } elseif ($l -match '^\s*\d+[.)]\s+(.*)$') { 'ol' } else { '' }
		if ($kind) {
			$item = $Matches[1]
			if (-not $list -or $list.k -ne $kind) { & $flush; $list = @{ k = $kind; items = (New-Object System.Collections.ArrayList) } }
			[void]$list.items.Add($item); continue
		}
		if ($list -and $l -match '^\s{2,}\S') { $list.items[$list.items.Count - 1] += ' ' + $l.Trim(); continue }   # list item continuation
		if ($list -or $tbl) { & $flush }
		[void]$para.Add($l.Trim())
	}
	& $flush
	return $out.ToArray()
}

# Inline markdown -> tokens @{k='text'|'code'|'bold'|'italic'|'link'; t; url}.
function Get-MdInlines {
	param([string]$Text)
	$rx = '`([^`]+)`|\*\*(.+?)\*\*|\[([^\]]+)\]\(([^)\s]+)\)|(?<![\*\w])\*(?![\s\*])(.+?)(?<![\s\*])\*(?!\*)'
	$out = @(); $at = 0
	foreach ($m in [regex]::Matches($Text, $rx)) {
		if ($m.Index -gt $at) { $out += @{ k = 'text'; t = $Text.Substring($at, $m.Index - $at) } }
		if ($m.Groups[1].Success) { $out += @{ k = 'code'; t = $m.Groups[1].Value } }
		elseif ($m.Groups[2].Success) { $out += @{ k = 'bold'; t = $m.Groups[2].Value } }
		elseif ($m.Groups[3].Success) { $out += @{ k = 'link'; t = $m.Groups[3].Value; url = $m.Groups[4].Value } }
		else { $out += @{ k = 'italic'; t = $m.Groups[5].Value } }
		$at = $m.Index + $m.Length
	}
	if ($at -lt $Text.Length) { $out += @{ k = 'text'; t = $Text.Substring($at) } }
	return $out
}

# A runbook code block run: the block goes into <out>/<step>-<n>.ps1 (no quoting
# problems), a wrapper runs it in $Cwd and appends every output line to the
# .log as it comes (flushed per line, so the window can tail it), then writes
# the exit code to .exit. Returns @{ proc; log; exit; start; n }.
function Start-BenchStepRun {
	param([string]$Command, [string]$Cwd, [string]$OutDir, [string]$Step, [string]$Exe = 'powershell.exe', [string]$Echo = '')
	if (-not $Echo) { $Echo = $Command }   # the log starts with what the tester saw (an action fence's text, not its script)
	New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
	$n = 1; while (Test-Path -LiteralPath "$OutDir/$Step-$n.log") { $n++ }
	$tmp = Join-Path ([IO.Path]::GetTempPath()) ('gitsp-run-' + [guid]::NewGuid().ToString('N')); New-Item -ItemType Directory -Path $tmp -Force | Out-Null
	$base = "$tmp/$Step-$n"; $log = "$OutDir/$Step-$n.log"; $q = { param($s) "'" + $s.Replace("'", "''") + "'" }   # scripts and .exit in temp: only the .log is pushed
	[IO.File]::WriteAllText("$base.ps1", $Command, (New-Object System.Text.UTF8Encoding $true))   # BOM: 5.1 reads it as UTF-8
	[IO.File]::WriteAllText($log, "> $($Echo -replace "`r?`n", "`r`n> ")`r`n", (New-Object System.Text.UTF8Encoding $false))
	$wrap = @"
`$ErrorActionPreference = 'Continue'
Set-Location -LiteralPath $(& $q $Cwd)
`$code = 0
try { & $(& $q "$base.ps1") *>&1 | ForEach-Object { [IO.File]::AppendAllText($(& $q $log), "`$_`r`n") }; if (`$LASTEXITCODE) { `$code = `$LASTEXITCODE } } catch { [IO.File]::AppendAllText($(& $q $log), "ERROR: `$_`r`n"); `$code = 1 }
[IO.File]::WriteAllText($(& $q "$base.exit"), [string]`$code)
"@
	[IO.File]::WriteAllText("$base-wrap.ps1", $wrap, (New-Object System.Text.UTF8Encoding $true))
	$sp = @{ FilePath = $Exe; ArgumentList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$base-wrap.ps1`""); PassThru = $true }
	if ($IsWindows -or $PSVersionTable.PSEdition -eq 'Desktop') { $sp.WindowStyle = 'Hidden' }
	$p = Start-Process @sp
	return @{ proc = $p; log = $log; exit = "$base.exit"; start = (Get-Date).ToUniversalTime().AddSeconds(-2); n = $n; step = $Step }
}

# New text in a log from byte $Offset (the file may still be written): @{ text; offset }.
function Read-BenchLogTail {
	param([string]$Path, [long]$Offset)
	if (-not (Test-Path -LiteralPath $Path)) { return @{ text = ''; offset = $Offset } }
	$fs = New-Object System.IO.FileStream $Path, 'Open', 'Read', 'ReadWrite'
	try {
		if ($fs.Length -lt $Offset) { $Offset = 0 }   # file replaced
		[void]$fs.Seek($Offset, 'Begin'); $buf = New-Object byte[] ($fs.Length - $Offset)
		$got = $fs.Read($buf, 0, $buf.Length)
		return @{ text = [Text.Encoding]::UTF8.GetString($buf, 0, $got); offset = $Offset + $got }
	} finally { $fs.Dispose() }
}

function Stop-BenchStepRun {
	param($Job)
	if (-not $Job -or -not $Job.proc -or $Job.proc.HasExited) { return }
	$ErrorActionPreference = 'Continue'   # 5.1: taskkill stderr ("not found") must not become a terminating error
	if ($IsWindows -or $PSVersionTable.PSEdition -eq 'Desktop') { & taskkill.exe /T /F /PID $Job.proc.Id 2>&1 | Out-Null } else { try { $Job.proc.Kill() } catch { } }
}

# Files under $Root written at or after $Since (UTC), as /-relative paths; .git and bench-run/out skipped.
function Get-BenchNewFiles {
	param([string]$Root, [datetime]$Since, [hashtable]$Skip = @{})
	$r = ($Root -replace '\\', '/').TrimEnd('/')
	foreach ($fi in @(Get-ChildItem -LiteralPath $Root -Recurse -File -Force -ErrorAction SilentlyContinue)) {
		$f = ($fi.FullName -replace '\\', '/').Substring($r.Length + 1)
		if ($f.StartsWith('.git/') -or $f -eq '.git' -or $f.StartsWith('bench-run/') -or $f.StartsWith('logs/acad/') -or $Skip[$f]) { continue }   # tracked files go in bench.patch; AutoCAD logs in per-step slices
		if ($fi.LastWriteTimeUtc -ge $Since) { $f }
	}
}

# BENCH verdict lines (plan 30 section 3.3, S6, V1, V2): 'BENCH <step> PASS|FAIL|INFO <reason> [abs path, / slashes]' and
# 'BENCH <step> END n=<checks>'. A line the format refuses (reason over 120 chars without the path, a ';', a
# backslash) is bad and FAILs the step. -> @{ checks; bad; end (n or $null); pass; fail }
function ConvertFrom-BenchLine {
	param([string]$Text, [string]$Step)
	$r = @{ checks = @(); bad = @(); end = $null; pass = 0; fail = 0 }
	foreach ($l in ($Text -split "`r?`n")) {
		if ($l -cnotmatch '^\s*(?:!! |ok )?BENCH\s+(\S+)\s+(\S+)\s*(.*?)\s*$') { continue }
		$sid = $Matches[1]; $v = $Matches[2]; $rest = $Matches[3]
		if ($v -ceq 'PROGRESS') { continue }   # 'BENCH <step> PROGRESS n/m': the progress bar, not a check
		if ($Step -and $sid -cne $Step -and $sid -cne 'LOAD') { continue }
		$own = -not $Step -or $sid -ceq $Step   # LOAD lines may FAIL a step, never count toward its PASS or END
		if ($v -ceq 'END') {
			if (-not $own) { continue }
			if ($null -ne $r.end -or $rest -cnotmatch '^n=(\d+)$') { $r.bad += $l.Trim() } else { $r.end = [int]$Matches[1] }
			continue
		}
		$path = ''; $why = $rest
		if ($rest -match '^(.*?)\s+((?:[A-Za-z]:)?/.*)$') { $why = $Matches[1]; $path = $Matches[2] }   # path: to line end
		$fmt = $v -cin 'PASS', 'FAIL', 'INFO' -and $why -match '\S' -and $why.Length -le 120
		if (-not $fmt -or $rest -match ';' -or $rest -match '\\' -or ($own -and $null -ne $r.end)) {
			$r.bad += $l.Trim(); continue   # a check after END is bad too
		}
		$r.checks += @{ step = $sid; verdict = $v; reason = $why; path = $path }
		if ($v -ceq 'FAIL') { $r.fail++ } elseif ($v -ceq 'PASS' -and $own) { $r.pass++ }
	}
	return $r
}

# The BENCH verdict of a step's output (plan 30 V1): fail on any FAIL, a bad line, or (-Auto) no END / a count that
# does not add up / an AutoCAD error line; pass only for -Auto with END n >= 1 and n PASS lines. -> @{ result; why }
function Get-BenchVerdict {
	param([string]$Text, [string]$Step, [switch]$Auto)
	$b = ConvertFrom-BenchLine -Text $Text -Step $Step
	if ($b.bad.Count) { return @{ result = 'fail'; why = "bad BENCH line: $($b.bad[0])" } }
	if ($b.fail) {
		$f = @($b.checks | Where-Object { $_.verdict -eq 'FAIL' })[0]
		return @{ result = 'fail'; why = "BENCH FAIL: $($f.reason)" }
	}
	if (-not $Auto) { return @{ result = ''; why = '' } }
	if ($null -eq $b.end) { return @{ result = 'fail'; why = 'no END: the step did not finish' } }
	if ($b.end -lt 1 -or $b.pass -ne $b.end) {
		return @{ result = 'fail'; why = "END n=$($b.end) but $($b.pass) PASS line(s)" }
	}
	$err = @(Get-BenchErrorLines $Text | Where-Object { $_ -notmatch '^(?:!! |ok )?BENCH ' })
	if ($err.Count) { return @{ result = 'fail'; why = "AutoCAD error: $($err[0])" } }
	return @{ result = 'pass'; why = "END n=$($b.end), all PASS" }
}

# Executor (plan 30 S12, brief R1/R2). The forms an auto step sends: its lisp and acad blocks, in order.
function Get-BenchAutoForm {
	param($Step)
	$sg = @(Get-RunbookSegments -Lines @($Step.body) | Where-Object { $_.act -in 'lisp', 'acad' })
	return @($sg | ForEach-Object { @{ kind = [string]$_.act; text = [string]$_.text } })
}

# The output of THIS run of an auto step (ust review H1): the text after the last 'BENCH <step> INFO begin <nonce>'
# line; '' when the marker has not come yet.
function Select-BenchRunText {
	param([string]$Text, [string]$Step, [string]$Nonce)
	$rx = '(?m)^\s*BENCH ' + [regex]::Escape($Step) + ' INFO begin ' + [regex]::Escape($Nonce) + '\s*$'
	$m = [regex]::Matches($Text, $rx)
	if (-not $m.Count) { return '' }
	return $Text.Substring($m[$m.Count - 1].Index)
}

# The begin marker line the send script writes into <step>.result (ust review C1: AutoCAD echoes a princ form, so a
# marker sent through AutoCAD never matched).
function Get-BenchBeginLine {
	param([string]$Step, [string]$Nonce)
	return "BENCH $Step INFO begin $Nonce"
}

# The next step of a lane run (ust review H4, M5): stop after a step that did not PASS; an answered step that is not
# auto is passed over; an unanswered one stops the lane there. -> @{ next = id or ''; why = '' or the stop note }
function Get-BenchLaneNext {
	param([string[]]$Order, [hashtable]$Types, $State, [string]$Current)
	$cr = if ($State.answers[$Current]) { [string]$State.answers[$Current].result } else { '' }
	$cw = if ($cr) { $cr } else { 'no result' }
	if ($cr -ne 'pass') { return @{ next = ''; why = "lane stopped at $Current ($cw)" } }
	$i = [Array]::IndexOf($Order, $Current)
	for ($j = $i + 1; $j -lt $Order.Count; $j++) {
		$id = $Order[$j]
		if ([string]$Types[$id] -eq 'auto') { return @{ next = $id; why = '' } }
		$r = if ($State.answers[$id]) { [string]$State.answers[$id].result } else { '' }
		if (-not $r) { return @{ next = ''; why = "lane stopped at $id ($($Types[$id]) step: it needs you)" } }
	}
	return @{ next = ''; why = 'lane done' }
}

# The step's END line is in its output.
function Test-BenchEndSeen {
	param([string]$Text, [string]$Step)
	return ($null -ne (ConvertFrom-BenchLine -Text $Text -Step $Step).end)
}

# The verdict of one auto run (D2, V1; ust review H3): a failed send or a block left unsent = FAIL; no END by the
# deadline = FAIL; else the -Auto verdict; a PASS with a bench block is BLOCKED. -> @{ result; why }
function Get-BenchAutoResult {
	param([string]$Text, [string]$Step, [bool]$TimedOut, [string[]]$Block = @(), [int]$Timeout = 120, [int]$Unsent = 0,
		[string]$SendExit = '0', [string]$SendLine = '')
	$sl = if ($SendLine) { $SendLine } else { "exit $SendExit" }
	if ($SendExit -ne '0') { return @{ result = 'fail'; why = "send failed: $sl" } }
	if ($Unsent -gt 0) { return @{ result = 'fail'; why = "$Unsent block(s) not sent" } }
	if ($TimedOut -and -not (Test-BenchEndSeen -Text $Text -Step $Step)) {
		return @{ result = 'fail'; why = "no END within $Timeout s" }
	}
	$v = Get-BenchVerdict -Text $Text -Step $Step -Auto
	if ($v.result -eq 'pass' -and @($Block | Where-Object { $_ }).Count) {
		return @{ result = 'blocked'; why = @($Block)[0] }
	}
	return @{ result = $v.result; why = $v.why }
}

# When a step's output last changed (ust review round 4 #3): its run logs, its result file, and its AutoCAD slice only
# when the last visit has lines (a revisit header alone is not output).
function Get-BenchOutTime {
	param([string]$Dir, [string]$Id)
	$t = [datetime]::MinValue
	$rx = '^' + [regex]::Escape($Id) + '-\d+\.log$'
	foreach ($f in @(Get-ChildItem -LiteralPath $Dir -File -ErrorAction SilentlyContinue)) {
		$mine = $f.Name -match $rx -or $f.Name -eq "$Id.result"
		if ($f.Name -eq "$Id-acad.log") {
			$lv = Get-BenchLastVisit ([IO.File]::ReadAllText($f.FullName))
			$mine = [bool](@($lv -split "`r?`n" | Where-Object { $_.Trim() -and $_ -notmatch '^=== step opened ' }).Count)
		}
		if ($mine -and $f.LastWriteTime -gt $t) { $t = $f.LastWriteTime }
	}
	return $t
}

# A step's output for checks (ust review N2): its newest run log <id>-<n>.log and the last visit of <id>-acad.log.
function Get-BenchStepText {
	param([string]$Dir, [string]$Id)
	$t = @()
	$rx = '^' + [regex]::Escape($Id) + '-\d+\.log$'
	$runs = @(Get-ChildItem -LiteralPath $Dir -Filter "$Id-*.log" -ErrorAction SilentlyContinue)
	$runs = @($runs | Where-Object { $_.Name -match $rx })
	$runs = @($runs | Sort-Object LastWriteTime)
	if ($runs.Count) { $t += [IO.File]::ReadAllText($runs[-1].FullName) }
	$al = Join-Path $Dir "$Id-acad.log"
	if (Test-Path -LiteralPath $al) { $t += Get-BenchLastVisit ([IO.File]::ReadAllText($al)) }
	$rf = Join-Path $Dir "$Id.result"   # brief R2: UST's result file for the step
	if (Test-Path -LiteralPath $rf) { $t += [IO.File]::ReadAllText($rf) }
	$rp = Join-Path $Dir "$Id.report"   # report=: BENCH lines made from the step's report file (Import-BenchReport)
	if (Test-Path -LiteralPath $rp) { $t += [IO.File]::ReadAllText($rp) }
	return ($t -join "`n")
}

# Window header (plan 30 S10, ust manual #9): full paths of the run folder, its logs and the main clone.
function Get-BenchHeader {
	param([string]$RunDir, [string]$Main = '')
	$f = { param($p) ([IO.Path]::GetFullPath($p) -replace '/', '\') }
	$h = "run $(& $f $RunDir)   logs $(& $f (Join-Path $RunDir 'logs'))"
	if ($Main) { $h += "   main $(& $f $Main)" }
	return $h
}

# The lane line (plan 30 S10, ust review V5): every count, and green only when every live step PASSed in this run.
function Get-BenchTally {
	param([string[]]$Ids, $State, [int]$Settled = 0)
	$c = [ordered]@{ pass = 0; fail = 0; blocked = 0; na = 0; pending = 0 }
	foreach ($id in $Ids) {
		$r = if ($State.answers[$id]) { [string]$State.answers[$id].result } else { '' }
		if ($c.Contains($r) -and $r) { $c[$r]++ } else { $c.pending++ }
	}
	$t = "pass $($c.pass)  fail $($c.fail)  blocked $($c.blocked)  n/a $($c.na)  not run $($c.pending)  of $($Ids.Count)"
	if ($Settled) { $t += "    settled $Settled" }
	$all = $Ids.Count -and $c.pass -eq $Ids.Count   # owner 2026-11-06: plain ALL PASS only with nothing settled
	if ($all -and $Settled) { return "$t    ALL LIVE PASS, $Settled settled" }
	return $t + $(if ($all) { '    ALL PASS' } else { '' })
}

# An auto run left pending when the window closed (ust review M7, N5) is FAIL at the next open, inside its deadline
# or not: no window waits for it any more. An answered step only loses its stale pending. -> the step ids made FAIL
function Close-BenchPendingRun {
	param($State)
	$ch = @()
	foreach ($k in @($State.answers.Keys)) {
		$a = $State.answers[$k]
		if (-not $a.pending) { continue }
		$a.pending = ''
		if ($a.result) { continue }
		$a.result = 'fail'; $a.judge = ''
		$a.note = ([string]$a.note + "`r`nauto: FAIL window closed while waiting").TrimStart(); $ch += $k
	}
	return $ch
}

# What a BENCH verdict does to a step's answer (ust review N1): FAIL is set when the step has no answer or the
# output changed after the answer; PASS (auto steps, D2) only when the step has no answer. -> 'fail' | 'pass' | ''
function Get-BenchAutoAnswer {
	param($Verdict, $Answer, [datetime]$OutTime = [datetime]::MinValue)
	if (-not $Verdict.result) { return '' }
	$at = ConvertFrom-BenchIsoText (ConvertTo-BenchIsoText $Answer.at)
	$open = -not $Answer.result
	if ($Verdict.result -eq 'fail' -and $Answer.result -ne 'fail' -and ($open -or $OutTime -gt $at)) { return 'fail' }
	if ($Verdict.result -eq 'pass' -and $open) { return 'pass' }
	return ''
}

# Text appended to a step's AutoCAD slice (ust review N3, N11): a visit header starts on its own line even when
# the file ends mid-line. $TailLf: the file is empty or ends with a line feed.
function Get-BenchSliceText {
	param([string]$Text, [bool]$Head, [datetime]$Opened, [bool]$TailLf = $true)
	if (-not $Head) { return $Text }
	$lead = if ($TailLf) { '' } else { "`r`n" }
	return $lead + (Get-BenchVisitHead $Opened) + "`r`n" + $Text
}

# Visit sections of a step's AutoCAD slice (plan 30 S5, ust R1510 O4: a re-opened step showed an earlier visit's lines).
# A file that does not exist, is empty, or ends with a line feed.
function Test-BenchTailLf {
	param([string]$Path)
	$f = Get-Item -LiteralPath $Path -ErrorAction SilentlyContinue
	if (-not $f -or $f.Length -eq 0) { return $true }
	$fs = [IO.File]::OpenRead($f.FullName)
	try { [void]$fs.Seek(-1, 'End'); return ($fs.ReadByte() -eq 10) } finally { $fs.Dispose() }
}

function Get-BenchVisitHead {
	param([datetime]$Opened)
	return "=== step opened $($Opened.ToString('yyyy-MM-dd HH:mm:ss')) ==="
}
# The text after the last visit header ($Text when it has none).
function Get-BenchLastVisit {
	param([string]$Text)
	$m = [regex]::Matches($Text, '(?m)^=== step opened [^\r\n]* ===\r?$')
	if (-not $m.Count) { return $Text }
	$l = $m[$m.Count - 1]
	return $Text.Substring($l.Index)
}

# AutoCAD command-line logs (plan 20 S4): name -> length of every *.log in $Dir.
function Get-BenchAcadLogSizes {
	param([string]$Dir)
	$h = @{}
	foreach ($f in @(Get-ChildItem -LiteralPath $Dir -Filter '*.log' -File -ErrorAction SilentlyContinue)) { $h[$f.Name] = $f.Length }
	return $h
}

# Text AutoCAD added to its logs since $Sizes (new files in full), oldest file first: @{ text; sizes = where each read stopped }.
function Get-BenchAcadLogSlice {
	param([string]$Dir, [hashtable]$Sizes)
	$sb = New-Object System.Text.StringBuilder; $end = @{} + $Sizes
	foreach ($f in @(Get-ChildItem -LiteralPath $Dir -Filter '*.log' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime)) {
		$from = if ($Sizes.ContainsKey($f.Name)) { [long]$Sizes[$f.Name] } else { 0 }
		if ($f.Length -le $from) { $end[$f.Name] = [Math]::Max($from, $f.Length); continue }
		$t = Read-BenchLogTail -Path $f.FullName -Offset $from
		[void]$sb.Append($t.text); $end[$f.Name] = $t.offset   # where this read stopped: lines written meanwhile come next time
	}
	return @{ text = $sb.ToString(); sizes = $end }
}

# <run>\bench-run\acad-status.txt (written by the bundle at each drawing load) -> hashtable, or $null.
function Read-BenchAcadStatus {
	param([string]$Path)
	if (-not (Test-Path -LiteralPath $Path)) { return $null }
	$h = @{}
	foreach ($l in @(Get-Content -LiteralPath $Path -ErrorAction SilentlyContinue)) {
		if ($l -match '^([\w-]+)=(.*)$') { $h[$Matches[1]] = $Matches[2] }   # [\w-]: support-first has a -
	}
	return $h
}

# <run>\bench-run\load-result.txt, written by the run's own load file: 'loaded <build>' or 'refused <reason>'.
# -> its first line, '' when absent or older than $Since (local time).
function Read-BenchLoadResult {
	param([string]$RunDir, [datetime]$Since)
	$f = Get-Item -LiteralPath "$RunDir/bench-run/load-result.txt" -ErrorAction SilentlyContinue
	if (-not $f -or $f.LastWriteTime -lt $Since) { return '' }
	return ([string]@(Get-Content -LiteralPath $f.FullName)[0]).Trim()
}

# What is wrong with AutoCAD for this step (plan 20 S5): a list of short lines.
# $Running: acad.exe is running; $Status: Read-BenchAcadStatus; $Since: when the step was opened (local time).
function Get-BenchStateIssues {
	param($Step, [bool]$Running, $Status, [string]$RunDir, [datetime]$Since)
	$out = @()
	$norm = { param($p) ([string]$p -replace '/', '\').TrimEnd('\').ToUpperInvariant() }
	$lr = Read-BenchLoadResult -RunDir $RunDir -Since $Since
	if ($lr -like 'refused*') { $out += "The run's load file $lr" }
	$need = if ($Step) { [string]$Step.restart } else { '' }
	if ($need -eq 'closed' -and $Running) { $out += 'This step needs AutoCAD CLOSED: close AutoCAD first.' }
	if ($need -in 'open', 'acad' -and -not $Running) { $out += 'This step needs AutoCAD OPEN: start AutoCAD.' }
	if ($need -eq 'acad' -and $Running) {
		$t = [datetime]::MinValue
		if (-not ($Status -and [datetime]::TryParse([string]$Status.time, [ref]$t)) -or $t -lt $Since) { $out += 'This step needs a FRESH AutoCAD: restart AutoCAD (no drawing was opened since this step started).' }
	}
	if ($Running -and $Status) {
		if ($Status.run -and (& $norm $Status.run) -ne (& $norm $RunDir)) { $out += "AutoCAD has another run folder loaded ($($Status.run)): open a new drawing." }
		if ([string]$Status.load -like 'fail*') {
			$why = ([string]$Status.load).Substring(4).Trim()
			$out += "The bench load file FAILED to load in AutoCAD ($(if ($why) { $why } else { 'see the AutoCAD command line' }))."
		}
		if ($Status.trusted -eq 'no' -and $Status.secureload -and $Status.secureload -ne '0') { $out += 'The bench bundle folder is not trusted and SECURELOAD is on: AutoCAD may block it.' }
	}
	# last ERROR line of the latest session in either trace (the bundle's and the load file's)
	foreach ($n in 'bundle', 'acaddoc') {
		$ls = @(Get-Content -LiteralPath "$RunDir/logs/bench-trace-$n.log" -ErrorAction SilentlyContinue)
		if (-not $ls.Count) { continue }
		$from = [Math]::Max(0, [array]::FindLastIndex($ls, [Predicate[string]]{ param($x) $x -match '\] (START|RUN) ' }))
		$e = @($ls[$from..($ls.Count - 1)] | Where-Object { $_ -match '\] ERROR ' }) | Select-Object -Last 1
		if ($e) { $out += "$(Get-BenchFullPath -Dir $RunDir -Rel "logs/bench-trace-$n.log"): $e" }
	}
	return $out
}

# Bench judge (plan 30 S1, ust R1810 A2): why a step run in this AutoCAD cannot PASS; empty = it can.
# $Status: Read-BenchAcadStatus of the run; $Expected: the expected build ('' = not checked).
# $Nonce / $Started: bench-run/acad-nonce.txt of the last Start AutoCAD ('' = no check); $Hwnd: the running
# AutoCAD's main window handle (0 = no check).
function Get-BenchJudge {
	param($Status, [string]$RunDir, [string]$Expected = '', [string]$Nonce = '', [datetime]$Started = [datetime]::MinValue,
		[long]$Hwnd = 0, [int]$Procs = -1)
	$norm = { param($p) ([string]$p -replace '/', '\').TrimEnd('\').ToUpperInvariant() }
	if (-not $Status) { return @('no bench-run/acad-status.txt: the bench bundle never ran in this AutoCAD') }
	$out = @()
	$t = [datetime]::MinValue; [void][datetime]::TryParse([string]$Status.time, [ref]$t)
	$nn = 'acad-status.txt is not from the AutoCAD that Start AutoCAD started (nonce)'
	if ($Nonce -and $Status.nonce -ne $Nonce) { $out += $nn }
	elseif ($Nonce -and $Started -ne [datetime]::MinValue -and $t -lt $Started.AddSeconds(-2)) {
		$out += 'acad-status.txt is older than this AutoCAD start'
	}
	# ust review M3: with a nonce, the window must be checkable: one AutoCAD, a handle, an hwnd= in the status
	if ($Nonce -and $Procs -gt 1) { $out += "$Procs AutoCAD processes run: close all but the bench one" }
	elseif ($Nonce -and $Procs -eq 1 -and -not $Hwnd) { $out += 'the AutoCAD window handle is not readable yet' }
	elseif ($Nonce -and $Procs -eq 1 -and -not $Status.hwnd) { $out += 'acad-status.txt has no hwnd= (an old bundle)' }
	elseif ($Hwnd -and [string]$Status.hwnd -ne [string]$Hwnd) { $out += 'acad-status.txt is from another AutoCAD window' }
	$nb = 'not a bench AutoCAD (bench=no): start AutoCAD with the window''s Start AutoCAD'
	if ($Status.bench -ne 'yes') { $out += $nb }
	elseif ((& $norm $Status.run) -ne (& $norm $RunDir)) { $out += "AutoCAD has another run loaded: $($Status.run)" }
	if ($Status.bench -eq 'yes' -and (& $norm $Status.'support-first') -ne (& $norm $RunDir)) {
		$out += "the support path does not start with the run folder (first: $($Status.'support-first'))"
	}
	if ($Status.bench -eq 'yes' -and $Status.load -ne 'ok') {
		$out += "the run's load file did not load (load=$($Status.load))"
	}
	$built = '^loaded ' + [regex]::Escape($Expected) + '(\s|$)'
	if ($Status.bench -eq 'yes' -and $Expected -and ([string]$Status.result).Trim() -notmatch $built) {
		$out += "UST load result is '$($Status.result)', expected 'loaded $Expected'"
	}
	return $out
}

# A step used AutoCAD (plan 30 S1, ust review H3): it declares it (restart= open|acad, or a lisp/acad/open/start-acad
# fence), its AutoCAD slice has text, or AutoCAD was seen running while it was open. Never: AutoCAD runs at PASS time.
function Test-BenchStepTouched {
	param($Step, [bool]$Slice = $false, [bool]$SeenRunning = $false)
	if ($Slice -or $SeenRunning) { return $true }
	if (-not $Step) { return $false }
	if ([string]$Step.restart -in 'open', 'acad') { return $true }
	$acts = @(Get-RunbookSegments -Lines @($Step.body) | ForEach-Object { $_.act } | Where-Object { $_ })
	return [bool](@($acts | Where-Object { $_ -in 'lisp', 'acad', 'open', 'start-acad' }).Count)
}

# The one rule every answer path uses (plan 30, ust review N1/Q2): a PASS with a block is refused; anything else
# stands. -> @{ result ('' when refused); message }
function Resolve-BenchAnswer {
	param([string]$Result, [string[]]$Block = @(), [string]$Text = '', [string]$Step = '', [switch]$Auto)
	if ($Result -eq 'pass' -and @($Block | Where-Object { $_ }).Count) {
		return @{ result = ''; message = "PASS refused (bench judge):`n" + (@($Block) -join "`n"); note = '' }
	}
	$note = ''
	# plan 30 S10 / round 4 #9: a skipped step's logs are judged into the note
	if ($Result -eq 'na' -and $Step) {
		$sv = Get-BenchVerdict -Text $Text -Step $Step -Auto:$Auto
		$note = if ($sv.result) { "skipped; logs say: $($sv.why)" } else { 'skipped; no BENCH verdict in the logs' }
	}
	return @{ result = $Result; message = ''; note = $note }
}

# Why a PASS is refused (plan 30 S1): a BENCH FAIL or bad line in the step's output ($Text, its last visit), then,
# for a step that used AutoCAD, the bench judge, the expected build, and every drawing load of this AutoCAD session
# since $Since (ust review H2). Empty = PASS allowed. Shared by every PASS path and the push.
function Get-BenchPassBlock {
	param([string]$RunDir, [string]$Stamp, [bool]$Touched, [datetime]$Since = [datetime]::MinValue, [string]$Text = '',
		[string]$Step = '')
	$out = @()
	if ($Text -and $Step) {
		$bv = Get-BenchVerdict -Text $Text -Step $Step   # the step text already holds only the last AutoCAD visit
		if ($bv.result -eq 'fail') { $out += $bv.why }
	}
	if (-not $Touched) { return $out }
	$st = Read-BenchAcadStatus "$RunDir/bench-run/acad-status.txt"
	$exp = Get-BenchExpectedStamp -RunDir $RunDir -Stamp $Stamp
	$ja = Get-BenchJudgeContext -RunDir $RunDir
	$out += @(Get-BenchJudge -Status $st -RunDir $RunDir -Expected $exp @ja)
	if ($Stamp -and -not $exp) { $out += "no expected build: $Stamp is missing in the run folder" }
	$dl = Get-BenchDocLoad -RunDir $RunDir -Status $st -Nonce ([string]$ja.Nonce) -Since $Since
	foreach ($k in $dl.other.Keys) { $out += "drawing $k did not load the run (load=$($dl.other[$k]))" }
	foreach ($d in @($dl.open | Where-Object { -not $dl.seen[$_.ToUpperInvariant()] })) {
		$out += "drawing $d is open but never loaded the bench run"
	}
	return $out
}

# Push-time judge (plan 30 S1, ust review M6c): a PASS row whose step has an AutoCAD slice
# (bench-run/out/<step>-acad.log) becomes BLOCKED when Get-BenchPassBlock refuses it. Changes the rows in place;
# -> one message per changed row.
# A PASS row with a BENCH FAIL in its step's output becomes FAIL. A row the window passed carries the judge snapshot
# taken then (results.json `judge`, ust review N5) and is not judged against the later AutoCAD state; any other PASS
# row with an AutoCAD slice is judged on the state at push.
function Invoke-BenchPushJudge {
	param($Rows, [string]$RunDir, [string]$Stamp, $State = $null)
	$msgs = @()
	foreach ($r in @($Rows)) {
		if ($r.result -ne 'pass') { continue }
		$id = if ($r.step) { [string]$r.step } else { [string]$r.task }
		$bv = Get-BenchVerdict -Text (Get-BenchStepText -Dir "$RunDir/bench-run/out" -Id $id) -Step $id
		if ($bv.result -eq 'fail') {
			$r.result = 'fail'; $r.note = ([string]$r.note + " [at push: $($bv.why)]").Trim()
			$msgs += "$id PASS -> FAIL: $($bv.why)"
			continue
		}
		$af = Get-Item -LiteralPath "$RunDir/bench-run/out/$id-acad.log" -ErrorAction SilentlyContinue
		$sa = if ($State -and $State.answers[$id]) { $State.answers[$id] } else { $null }
		if (Test-BenchSnapshot -Answer $sa -Nonce ([string](Get-BenchJudgeContext -RunDir $RunDir).Nonce) -SliceTime $(
				if ($af) { $af.LastWriteTime } else { [datetime]::MinValue })) { continue }
		if (-not ($af -and $af.Length -gt 0)) { continue }
		$jd = @(Get-BenchPassBlock -RunDir $RunDir -Stamp $Stamp -Touched $true)
		if (-not $jd.Count) { continue }
		$r.result = 'blocked'; $r.note = ([string]$r.note + " [bench judge at push: $($jd[0])]").Trim()
		$msgs += "$id PASS -> BLOCKED: $($jd[0])"
	}
	return $msgs
}

# A window-judged PASS still stands at push (ust review N5, round 4 #2): its snapshot names the AutoCAD session that
# is still the bench's (nonce) and nothing was captured for the step after the answer.
function Test-BenchSnapshot {
	param($Answer, [string]$Nonce, [datetime]$SliceTime = [datetime]::MinValue)
	if (-not $Answer -or [string]$Answer.judge -notmatch '^ok (\S*)$') { return $false }
	if (-not $Nonce -or $Matches[1] -ne $Nonce) { return $false }
	$at = ConvertFrom-BenchIsoText (ConvertTo-BenchIsoText $Answer.at)   # ust review N4: any culture, sub-seconds kept
	if ($at -eq [datetime]::MinValue) { return $false }
	return ($SliceTime -le $at)
}

# Nonce, start time and AutoCAD window handle for Get-BenchJudge (splat); empty when unknown.
function Get-BenchJudgeContext {
	param([string]$RunDir, $Acad = $null)   # $Acad: the acad.exe processes (tests pass stand-ins)
	$h = @{}
	$n = @(Get-Content -LiteralPath "$RunDir/bench-run/acad-nonce.txt" -ErrorAction SilentlyContinue)
	if ($n.Count -ge 2) {
		$h.Nonce = $n[0].Trim(); $t = [datetime]::MinValue
		if ([datetime]::TryParse($n[1], [ref]$t)) { $h.Started = $t }
	}
	$p = if ($null -ne $Acad) { @($Acad) } else { @(Get-Process -Name acad -ErrorAction SilentlyContinue) }
	$h.Procs = $p.Count
	if ($p.Count -eq 1) { $h.Hwnd = [long]$p[0].MainWindowHandle }
	# a status older than the running AutoCAD is never this session's; an elevated AutoCAD hides StartTime: the nonce
	# file time stays the bound
	# (ust review H2: PowerShell reads a throwing getter as $null, so the guard is the null check, not a try)
	if ($h.Nonce -and $p.Count -eq 1) {
		$pt = $p[0].StartTime
		if ($pt -and (-not $h.Started -or $pt -gt $h.Started)) { $h.Started = $pt }
	}
	return $h
}

# Drawings of the bench session (plan 30 S3): bench-run/acad-docs.txt lines of this nonce.
# -> @{ total = docs= of acad-status.txt (0 = unknown); loaded = paths with load=ok; other = path -> failed load;
#       seen = upper-case path -> $true }
function Get-BenchDocLoad {
	param([string]$RunDir, $Status, [string]$Nonce = '', [datetime]$Since = [datetime]::MinValue)
	$r = @{ total = 0; loaded = @(); other = [ordered]@{}; fails = @(); seen = @{}; okat = @{}; open = @() }
	if ($Status -and [string]$Status.docs -match '^\d+$') { $r.total = [int]$Status.docs }
	$r.open = @(if ($Status -and $Status.docpaths) { ([string]$Status.docpaths -split '\|') | Where-Object { $_ } })
	foreach ($l in @(Get-Content -LiteralPath "$RunDir/bench-run/acad-docs.txt" -ErrorAction SilentlyContinue)) {
		if ($l -notmatch '^nonce=(\S*) time=(\S+ \S+) load=(\S+) doc=(.+)$') { continue }
		$ln = $Matches[1]; $lt = $Matches[2]; $ld = $Matches[3]; $doc = $Matches[4].Trim()
		if ($Nonce -and $ln -ne $Nonce) { continue }
		$t = [datetime]::MinValue; [void][datetime]::TryParse($lt, [ref]$t)
		$r.seen[$doc.ToUpperInvariant()] = $true
		if ($ld -eq 'ok') {
			if ($r.loaded -notcontains $doc) { $r.loaded += $doc }
			if (-not $r.okat[$doc] -or $t -gt $r.okat[$doc]) { $r.okat[$doc] = $t }
			continue
		}
		# a failed load counts while it is the drawing's newest line, or when it happened during the step (1 s margin)
		$rec = $Since -ne [datetime]::MinValue -and $t -ge $Since.AddSeconds(-1)
		$r.fails += @{ doc = $doc; load = $ld; time = $t; recent = $rec }
	}
	foreach ($f in $r.fails) {
		$later = @($r.fails | Where-Object { $_.doc -eq $f.doc -and $_.time -gt $f.time }).Count
		$okLater = $r.okat[$f.doc] -and $r.okat[$f.doc] -gt $f.time
		if ($f.recent -or (-not $later -and -not $okLater)) { $r.other[$f.doc] = $f.load }
	}
	return $r
}

# expect / fail patterns (plan 20 S5) against a step's output. .NET regex, case-sensitive, multiline.
# -> @{ result = 'pass' | 'fail' | ''; hits = matching lines; missing = expect patterns with no match }
function Test-BenchExpect {
	param([string]$Text, [string[]]$Expect = @(), [string[]]$Fail = @())
	$hits = @(); $missing = @(); $failed = $false
	foreach ($p in @($Fail | Where-Object { $_ })) {
		$l = @(Find-BenchLine -Text $Text -Pattern $p -First)
		if ($l.Count) { $failed = $true; $hits += 'FAIL: ' + $l[0] }
	}
	foreach ($p in @($Expect | Where-Object { $_ })) {
		$l = @(Find-BenchLine -Text $Text -Pattern $p -First)
		if ($l.Count) { $hits += $l[0] } else { $missing += $p }
	}
	$r = if ($failed) { 'fail' } elseif (@($Expect | Where-Object { $_ }).Count -and -not $missing.Count) { 'pass' } else { '' }   # a missing expect is listed, not a FAIL: the output may not be complete yet
	return @{ result = $r; hits = $hits; missing = $missing }
}

# Which step was open when a file was written (plan 20 S6). $Spans: @{ step; from; to } in
# open order, to = $null for the step open now; $Time: local time. -> step id or ''.
function Get-BenchFileStep {
	param($Spans, [datetime]$Time)
	foreach ($s in @($Spans)) { if ($Time -ge $s.from -and ($null -eq $s.to -or $Time -lt $s.to)) { return [string]$s.step } }
	return ''
}

# Steps whose collect= globs match none of $Files: @('K1: logs/*usttest*.log', ...).
function Get-BenchMissingCollect {
	param($Steps, [string[]]$Files, [string]$Dir = '')
	foreach ($s in @($Steps)) {
		foreach ($g in @($s.collect)) {
			if (-not $g -or @($Files | Where-Object { Test-BenchGlob $_ $g }).Count) { continue }
			"$($s.id): $(if ($Dir) { Get-BenchFullPath -Dir $Dir -Rel $g } else { $g })"
		}
	}
}

# --- window model (ust review: every window handler is one call into these, testable with fake io) ----
# $M: State, steps, live, Rb, RunDir, OutDir (the run's bench-run), Stamp, Acad, Main, Exe, Vlx, acadDir, tracked,
# ui (the window state), io (scriptblocks for every side effect): msg (text, title), confirm (text, title -> bool),
# noteGet, noteSet (text), out (text), head (text), stop (enabled), save, refresh, view (obj, step), pane (id),
# errShow (id), expect (Test-BenchExpect result or $null), cutAcad, runJob (code, echo, step -> job or $null), now.

# ISO time text of a results.json value (ust review N4: pwsh 7 ConvertFrom-Json makes ISO strings DateTime, and
# [string] of one is the invariant MM/dd/yyyy without sub-seconds).
function ConvertTo-BenchIsoText {
	param($Value)
	if ($Value -is [datetime]) { return $Value.ToString('o') }
	return [string]$Value
}

# An ISO time read back in any culture; MinValue when empty or not a time.
function ConvertFrom-BenchIsoText {
	param([string]$Text)
	$t = [datetime]::MinValue
	$ic = [Globalization.CultureInfo]::InvariantCulture
	if (-not [datetime]::TryParse($Text, $ic, [Globalization.DateTimeStyles]::RoundtripKind, [ref]$t)) {
		return [datetime]::MinValue
	}
	return $t
}

# results.json `judge` of an answer (ust review N5): 'ok <nonce>' for a PASS (the snapshot the push trusts), else ''.
function Get-BenchJudgeMark {
	param($M, [string]$Result)
	if ($Result -ne 'pass') { return '' }
	return 'ok ' + [string](Get-BenchJudgeContext -RunDir $M.RunDir).Nonce
}

function Get-BenchModelStep {
	param($M, [string]$Id)
	return @($M.steps | Where-Object { $_.id -eq $Id })[0]
}

# The step's answer, made when it has none.
function Get-BenchAnswer {
	param($M, [string]$Id)
	$a = $M.State.answers[$Id]
	if (-not $a) { $a = @{ result = ''; note = ''; files = @() }; $M.State.answers[$Id] = $a }
	return $a
}

function Add-BenchAnswerFile {
	param($M, [string]$Rel, [string]$Id = '')
	if (-not $Id) { $Id = [string]$M.ui.cur }
	if (-not $Id) { return }
	$a = Get-BenchAnswer $M $Id
	if (@($a.files) -notcontains $Rel) { $a.files = @(@($a.files) + $Rel) }
	& $M.io.save
}

# Copy a file into the open step's attachments (ust review 05749b6 #8: Attach and paste). -> its Rel path, ''
# with no step.
function Add-BenchFileCopy {
	param($M, [string]$Src)
	$id = [string]$M.ui.cur
	if (-not $id) { return '' }
	$d = "$($M.OutDir)/files"; New-Item -ItemType Directory -Path $d -Force | Out-Null
	$name = "$id-$([IO.Path]::GetFileName($Src))"
	Copy-Item -LiteralPath $Src -Destination "$d/$name" -Force
	$rel = "bench-run/files/$name"; Add-BenchAnswerFile $M -Rel $rel -Id $id
	return $rel
}

# The close checks (ust review f1a3273 N2: before Abort or Push change any state): a waiting auto run asks first, then
# a running command (Yes stops it). -> $true to close
function Test-BenchCanClose {
	param($M)
	if (-not (Test-BenchCloseOk $M)) { return $false }
	$j = $M.ui.job
	if (-not $j -or $j.proc.HasExited) { return $true }
	if (-not (& $M.io.confirm 'A command is still running. Stop it and close?' 'Close')) { return $false }
	Stop-BenchStepRun $j
	return $true
}

# Abort the run (ust review 05749b6 #8): the reason is kept and saved, the exit is 'abort' (the push runs). -> $true
# to close; no reason, or a close check said no, changes nothing (f1a3273 N2).
function Invoke-BenchAbort {
	param($M, [string]$Reason)
	if (-not $Reason -or -not (Test-BenchCanClose $M)) { return $false }
	$M.State.abort = $Reason; & $M.io.save; $M.ui.exit = 'abort'; $M.ui.closing = $true
	return $true
}

# Push from the review page (f1a3273 N2): the close checks first, then the ticked files, saved, exit 'finish'. -> $true
# to close
function Invoke-BenchPushExit {
	param($M, [System.Collections.ArrayList]$Picked, $Items)
	if (-not (Test-BenchCanClose $M)) { return $false }
	$Picked.Clear(); foreach ($p in @(Get-BenchPicked $Items)) { [void]$Picked.Add($p) }
	& $M.io.save; $M.ui.exit = 'finish'; $M.ui.closing = $true
	return $true
}

# The review page's ticked files (ust review 05749b6 #3): the Tag of each item with IsChecked true; ':none:' when
# none is ticked (matches no file: the push sends the results only).
function Get-BenchPicked {
	param($Items)
	$p = @(foreach ($cb in @($Items)) {
			if ($cb -and $cb.PSObject.Properties['IsChecked'] -and $cb.IsChecked) { [string]$cb.Tag }
		})
	if (-not $p.Count) { $p = @(':none:') }
	return $p
}

# Get-BenchPassBlock for a step (plan 30 S1): judged when it used AutoCAD (Test-BenchStepTouched).
function Get-BenchStepJudge {
	param($M, [string]$Id)
	$s = Get-BenchModelStep $M $Id
	$af = Get-Item -LiteralPath "$($M.OutDir)/out/$Id-acad.log" -ErrorAction SilentlyContinue
	$sl = [bool]($af -and $af.Length -gt 0)
	$tc = Test-BenchStepTouched -Step $s -Slice $sl -SeenRunning ([bool]$M.ui.touched[$Id])
	$from = if ($M.ui.mark -and $M.ui.mark.step -eq $Id) { $M.ui.since } else { [datetime]::MinValue }
	$pb = @{ RunDir = $M.RunDir; Stamp = $M.Stamp; Touched = $tc; Since = $from; Step = $Id }
	return @(Get-BenchPassBlock @pb -Text (Get-BenchStepText -Dir "$($M.OutDir)/out" -Id $Id))
}

# ust review M9/N2: while an auto run waits only its step may be opened; '' = no step may be answered or changed.
# -> $true when refused (the output pane says why).
function Test-BenchAutoLock {
	param($M, [string]$Id = '')
	$au = $M.ui.auto
	if (-not $au -or ($Id -and $Id -eq $au.step)) { return $false }
	& $M.io.out "auto run of $($au.step) is waiting; press Stop to end it first"
	return $true
}

# Alt+P/F/B/N (plan 30 S1, S10): the judge first, Resolve-BenchAnswer decides, the answer clears a pending run (N5).
function Invoke-BenchAnswer {
	param($M, [string]$Result)
	$ui = $M.ui; $id = [string]$ui.cur
	if (-not $id -or (Test-BenchAutoLock $M)) { return }
	& $M.io.cutAcad
	$s = Get-BenchModelStep $M $id
	$rp = @{ Result = $Result; Block = @(Get-BenchStepJudge $M $id); Step = $id; Auto = [string]$s.type -eq 'auto' }
	$ra = Resolve-BenchAnswer @rp -Text (Get-BenchStepText -Dir "$($M.OutDir)/out" -Id $id)
	if (-not $ra.result) { & $M.io.msg ($ra.message + "`n`nMark it FAIL or BLOCKED.") 'Bench judge'; return }
	$note = [string](& $M.io.noteGet)
	if ($ra.note -and $note -notmatch [regex]::Escape($ra.note)) {
		$note = ($note.TrimEnd() + "`r`n" + $ra.note).TrimStart(); & $M.io.noteSet $note
	}
	$a = Get-BenchAnswer $M $id
	$a.result = $Result; $a.note = $note; $a.at = (& $M.io.now).ToString('o'); $a.pending = ''
	$a.judge = Get-BenchJudgeMark $M $Result
	$ui.reveal = $id; & $M.io.save; & $M.io.refresh
}

# Tree click, go, auto start: the lock is checked before ui.cur changes (ust review N2).
function Invoke-BenchSelect {
	param($M, [string]$Id)
	if (Test-BenchAutoLock $M $Id) { return }
	$M.ui.cur = $Id; & $M.io.refresh
	Invoke-BenchShow $M $Id
}

# +1/-1 steps; 0 = the next unanswered one.
function Invoke-BenchGo {
	param($M, [int]$By)
	$ids = @($M.live | ForEach-Object { $_.id }); if (-not $ids.Count) { return }
	$i = [Array]::IndexOf($ids, $M.ui.cur)
	if ($By -eq 0) {
		for ($k = 1; $k -le $ids.Count; $k++) {
			$j = ($i + $k) % $ids.Count; $a = $M.State.answers[$ids[$j]]
			if (-not ($a -and $a.result)) { $i = $j; break }
		}
	} else { $i = [Math]::Max(0, [Math]::Min($ids.Count - 1, $i + $By)) }
	Invoke-BenchSelect $M $ids[$i]
}

# Open a step (or a lane node 'g:<id>:...'): its AutoCAD capture starts, a revisit gets its own section at once
# (ust review N11), the Files span starts, the note and the page are shown, then the checks run.
function Invoke-BenchShow {
	param($M, [string]$Id)
	$ui = $M.ui
	if (Test-BenchAutoLock $M $Id) { return }
	$s = Get-BenchModelStep $M $Id
	$gid = if ($Id -match '^g:([^:]*)') { $Matches[1] } else { $null }
	$obj = if ($s) { $s } else { @($M.Rb.groups) | Where-Object { $_.id -eq $gid } | Select-Object -First 1 }
	if (-not $obj) { return }
	& $M.io.cutAcad
	$ui.cur = if ($s) { $s.id } else { $null }
	$ui.mark = if ($s) { @{ step = $s.id; sizes = (Get-BenchAcadLogSizes $M.acadDir); head = $true } } else { $null }
	$ui.since = & $M.io.now
	# since=lane (ust R20261109-1033): when the lane's first step was opened
	if ($null -eq $ui.laneSince) { $ui.laneSince = @{} }
	$lk = if ($s) { [string]$s.group } else { '' }
	if ($lk -and -not $ui.laneSince.ContainsKey($lk)) { $ui.laneSince[$lk] = $ui.since }
	$lf = "$($M.OutDir)/out/$Id-acad.log"
	if ($s -and (Test-Path -LiteralPath $lf)) {
		$hd = Get-BenchSliceText -Text '' -Head $true -Opened $ui.since -TailLf (Test-BenchTailLf $lf)
		[IO.File]::AppendAllText($lf, $hd); $ui.mark.head = $false
	}
	if ($ui.spans.Count) { $ui.spans[$ui.spans.Count - 1].to = $ui.since }
	if ($s) { [void]$ui.spans.Add(@{ step = $s.id; from = $ui.since; to = $null }) }
	$a = if ($s) { $M.State.answers[$s.id] } else { $null }
	& $M.io.noteSet $(if ($a) { [string]$a.note } else { '' })
	& $M.io.view $obj $s
	if ($s) { Invoke-BenchCheck $M $s.id }
}

# BENCH lines and expect checks of the open step (plan 30 S6, D2; ust review N1, N7): a BENCH FAIL is set at once,
# an auto PASS only for an open step the judge lets pass; the run's own verdict decides while its auto run waits.
function Invoke-BenchCheck {
	param($M, [string]$Id)
	$s = Get-BenchModelStep $M $Id
	if (-not $s -or $Id -ne $M.ui.cur) { return }
	$od = "$($M.OutDir)/out"
	$stx = Get-BenchStepText -Dir $od -Id $Id
	# -Auto once the step ran (ust review 4ad063b #9: a hand run without END is FAIL): its result file, or a BENCH line
	# of the step. AutoCAD lines alone (05749b6 #1) and a job log alone (Start AutoCAD, Restart; f1a3273 N1) are no run.
	$ot = Get-BenchOutTime -Dir $od -Id $Id
	# report=: the newest report since the step opened, into <out>/<id>.report and the Output pane
	if ($s.report) {
		# since=step (default): written since the step opened; lane: since its lane's first step opened; run: since the run
		$from = switch ([string]$s.since) {
			'run' { [datetime]$M.Since }
			'lane' {
				$ls = $M.ui.laneSince
				if ($ls -and $ls.ContainsKey([string]$s.group)) { $ls[[string]$s.group] } else { $M.ui.since }
			}
			default { $M.ui.since }
		}
		$rpa = @{ RunDir = $M.RunDir; OutDir = $od; Id = $Id; Glob = $s.report; Since = $from; Step = $s }
		$rpa.Lane = [string]$s.group
		# wait= or the larger of 30 min and twice the step's last exit-0 run (ust review B5)
		$last = Get-BenchLastDuration -Main $M.Main -Step $Id
		$rpa.WaitSec = if ($s.wait) { $s.wait } else { [int][Math]::Max(1800, 2 * $last) }
		# crash path (ust C3): AutoCAD was seen running in this step and is gone now
		$acadOn = [bool](Get-Process -Name acad -ErrorAction SilentlyContinue)
		$rpa.AcadGone = [bool]$M.ui.touched[$Id] -and -not $acadOn
		$rpa.Stopped = [string]$M.ui.repStop -eq $Id; if ($rpa.Stopped) { $M.ui.repStop = '' }
		$rpf = Import-BenchReport @rpa
		if ($rpf) {
			$stx = Get-BenchStepText -Dir $od -Id $Id
			& $M.io.out ("report $rpf`r`n" + ((Get-Content -LiteralPath "$od/$Id.report") -join "`r`n"))
		}
	}
	$ran = (Test-Path -LiteralPath "$od/$Id.result") -or $stx -match ('BENCH ' + [regex]::Escape($Id) + ' ')
	# a step judged from its report= files (any type, ust R20261109-1033) passes on its own like an auto step
	$rep = [bool]$s.report -and (Test-Path -LiteralPath "$od/$Id.report")
	$auto = ([string]$s.type -eq 'auto' -and $ran) -or $rep
	$bv = Get-BenchVerdict -Text $stx -Step $Id -Auto:$auto
	$a = Get-BenchAnswer $M $Id
	$newer = Get-BenchAutoAnswer -Verdict $bv -Answer $a -OutTime $ot
	if ($M.ui.auto -and $M.ui.auto.step -eq $Id) { $newer = '' }
	if ($newer -eq 'pass' -and @(Get-BenchStepJudge $M $Id).Count) { $newer = '' }
	if ($newer) {
		$note = [string](& $M.io.noteGet)
		# the note gets the BENCH lines once per verdict
		if ($a.benchwhy -ne $bv.why) {
			$bc = @((ConvertFrom-BenchLine -Text $stx -Step $Id).checks)
			$bl = @($bc | ForEach-Object { "BENCH $($_.verdict) $($_.reason)" })
			$note = ($note.TrimEnd() + "`r`n" + $bv.why + "`r`n" + ($bl -join "`r`n")).TrimStart()
			& $M.io.noteSet $note
		}
		$a.result = $newer; $a.benchwhy = $bv.why; $a.note = $note; $a.at = (& $M.io.now).ToString('o'); $a.pending = ''
		$a.judge = Get-BenchJudgeMark $M $newer
		& $M.io.save; & $M.io.refresh
	}
	if (-not (@($s.expect).Count + @($s.fail).Count)) { & $M.io.expect $null; return }
	& $M.io.expect (Test-BenchExpect -Text $stx -Expect @($s.expect) -Fail @($s.fail))
}

# New output on the hidden Output tab (owner 2026-11-09): a dot before Output, bold on amber, red when the new lines hold an
# error line; opening the tab clears it (-Clear). $Tab is the Output TabItem (any object with Header etc. in tests).
function Show-BenchOutFlag {
	param($Tab, [string]$Text = '', [switch]$Clear)
	if ($Clear -or $Tab.IsSelected) {
		$Tab.Header = 'Output'; $Tab.FontWeight = 'Normal'; $Tab.Background = $null; $Tab.Tag = $null; return
	}
	$err = $Text -match '(?m)^\s*(; error|.*\bFAIL\b|Error:)'
	if ($err) { $Tab.Tag = 'err' }
	$Tab.Header = [string][char]0x25CF + ' Output'; $Tab.FontWeight = 'Bold'
	$Tab.Background = $(if ($Tab.Tag -eq 'err') { '#FFF4B4B4' } else { '#FFFFE08A' })
}

# Progress of a running job (owner 2026-11-09), best source first: the last 'BENCH <step> PROGRESS n/m' line it
# printed; else elapsed time against the step's duration at its last exit-0 run; else none (a moving bar).
# -> @{ pct (0-100, -1 = unknown); text }.
function Get-BenchJobProgress {
	param([string]$Text, [string]$Step, [double]$Elapsed, [double]$LastSec)
	$mm = { param($s) '{0}:{1:00}' -f [int][Math]::Floor($s / 60), [int]($s % 60) }
	$rx = '(?m)^\s*(?:!! |ok )?BENCH\s+' + [regex]::Escape($Step) + '\s+PROGRESS\s+(\d+)/(\d+)'
	$p = @([regex]::Matches($Text, $rx)) | Select-Object -Last 1
	if ($p -and [int]$p.Groups[2].Value -gt 0) {
		$n = [int]$p.Groups[1].Value; $m = [int]$p.Groups[2].Value
		return @{ pct = [Math]::Min(100, [int](100 * $n / $m)); text = "$n/$m ($(& $mm $Elapsed))" }
	}
	if ($LastSec -gt 0) {
		$pct = [Math]::Min(99, [int](100 * $Elapsed / $LastSec))
		$over = if ($Elapsed -gt $LastSec) { ', over' } else { '' }
		return @{ pct = $pct; text = "~$pct% ($(& $mm $Elapsed) of ~$(& $mm $LastSec) last run$over)" }
	}
	return @{ pct = -1; text = "$(& $mm $Elapsed) (no earlier run to compare)" }
}

# Step durations of exit-0 runs, per main clone: <main>/.git/git-sp-bench-durations.tsv, 'step<TAB>seconds' lines.
function Get-BenchLastDuration {
	param([string]$Main, [string]$Step)
	$f = "$Main/.git/git-sp-bench-durations.tsv"
	$hit = @(Get-Content -LiteralPath $f -ErrorAction Ignore | Where-Object { $_ -like "$Step`t*" })
	$hit = $hit | Select-Object -Last 1
	if (-not $hit) { return 0 }
	return [double]($hit -split "`t")[1]
}

function Add-BenchDuration {
	param([string]$Main, [string]$Step, [double]$Seconds)
	if (-not $Main -or -not (Test-Path -LiteralPath "$Main/.git" -PathType Container)) { return }
	$line = "$Step`t$([Math]::Round($Seconds))`n"
	[IO.File]::AppendAllText("$Main/.git/git-sp-bench-durations.tsv", $line)
}

# mode=vlx|lsp on a step or its lane (ust 2026-11-09): a step whose own mode, else its lane's, is not the run's load
# mode is hidden, as a settled one is: out of the tree's open part, the tallies and the lanes. -> the hidden ids.
function Hide-BenchModeStep {
	param($Rb, [string]$Mode)
	$lm = @{}; foreach ($g in @($Rb.groups)) { if ($g.mode) { $lm[[string]$g.id] = [string]$g.mode } }
	$out = @()
	foreach ($s in @($Rb.steps)) {
		$m = if ($s.mode) { [string]$s.mode } else { [string]$lm[[string]$s.group] }
		if ($m -and $m -ne $Mode) { $s.hidden = $true; $out += $s.id }
	}
	return $out
}

# <run>/bench-run/current-step.txt: line 1 the step id, line 2 its lane id (plan 31 P3), for test code that
# runs outside a job (an AutoCAD already running reads gsb:step / gsb:lane; this file is the fallback).
function Write-BenchCurrentStep {
	param([string]$RunDir, [string]$Step, [string]$Lane)
	if (-not $RunDir) { return }
	New-Item -ItemType Directory -Force -Path "$RunDir/bench-run" | Out-Null
	[IO.File]::WriteAllText("$RunDir/bench-run/current-step.txt", "$Step`n$Lane`n")
}

# Run a block under a step (plan 20 S3). -> the job, or $null when refused (ust review N3).
function Invoke-BenchRunBlock {
	param($M, [string]$Code, [string]$Echo = '', [string]$StepId = '')
	$ui = $M.ui
	if (-not $StepId) { $StepId = [string]$ui.cur }   # an auto run names its own step (ust review M9)
	if (-not $StepId) { return $null }
	if ($ui.job) { & $M.io.msg 'A command is still running. Stop it first.' 'Run'; return $null }
	# plan 31 P3: the step and lane before the action: bench-run/current-step.txt and GSB_STEP / GSB_LANE in the job
	$lane = [string](Get-BenchModelStep $M $StepId).group
	Write-BenchCurrentStep -RunDir $M.RunDir -Step $StepId -Lane $lane
	$Code = "`$env:GSB_STEP = '$StepId'; `$env:GSB_LANE = '$lane'`r`n" + $Code
	$j = & $M.io.runJob $Code $Echo $StepId
	if (-not $j) { return $null }
	$ui.job = $j; $ui.part = ''; $ui.off = 0; $ui.jobText = ''
	$ui.jobLast = Get-BenchLastDuration -Main $M.Main -Step $StepId
	& $M.io.stop $true
	return $j
}

# An action fence's button (F4): its generated script through the Run machinery.
function Invoke-BenchActionRun {
	param($M, [string]$Kind, [string]$Text)
	if ($Kind -eq 'start-acad') { [void](Invoke-BenchRebuildRecheck -RunDir $M.RunDir -Vlx $M.Vlx -Stamp $M.Stamp) }
	$sa = @{ Kind = $Kind; Text = $Text; RunDir = $M.RunDir; Acad = $M.Acad; Main = $M.Main }
	if ($M.ui.cur) { $sa.StepId = [string]$M.ui.cur; $sa.LaneId = [string](Get-BenchModelStep $M $M.ui.cur).group }
	try { $sc = ConvertTo-BenchActionScript @sa }
	catch { & $M.io.out "Cannot run this $Kind block (step $($M.ui.cur)): $($_.Exception.Message)"; return }
	[void](Invoke-BenchRunBlock $M -Code $sc -Echo $Text)
}

# Alt+A (plan 30 S12): start an auto run; an error before it waits makes the step BLOCKED and ends the lane.
function Invoke-BenchAutoRun {
	param($M, [string]$Id)
	try { Invoke-BenchAutoStart $M $Id } catch {
		$a = Get-BenchAnswer $M $Id; $a.result = 'blocked'; $a.pending = ''; $a.judge = ''
		$a.note = ([string]$a.note + "`r`nauto run not started: $($_.Exception.Message)").TrimStart()
		$M.ui.auto = $null; $M.ui.lane = @(); & $M.io.stop ([bool]$M.ui.job); & $M.io.save; & $M.io.refresh
	}
}

# Judge, open the step (a new visit, ust review H2), mark the run pending, send the first block.
function Invoke-BenchAutoStart {
	param($M, [string]$Id)
	$ui = $M.ui
	if ($ui.auto) { & $M.io.out "auto run of $($ui.auto.step) is still waiting; press Stop to end it first"; return }
	$s = Get-BenchModelStep $M $Id
	if (-not $s -or [string]$s.type -ne 'auto') { & $M.io.out "$Id is not an auto step"; $ui.lane = @(); return }
	if ($ui.job) { & $M.io.out 'A command is still running. Stop it first.'; $ui.lane = @(); return }
	$bk = @(Get-BenchPassBlock -RunDir $M.RunDir -Stamp $M.Stamp -Touched $true)
	$fm = @(Get-BenchAutoForm -Step $s)
	if (-not $fm.Count) { $bk += 'this auto step has no lisp or acad block' }
	$a = Get-BenchAnswer $M $Id
	if ($bk.Count) {
		$a.result = 'blocked'; $a.pending = ''; $a.judge = ''; $a.at = (& $M.io.now).ToString('o')
		$a.note = ([string]$a.note + "`r`nauto run not started: $($bk[0])").TrimStart()
		& $M.io.save; & $M.io.refresh; $ui.lane = @(); return
	}
	$to = if ([int]$s.timeout -gt 0) { [int]$s.timeout } else { 120 }
	$fresh = $ui.cur -ne $Id -or -not $ui.mark -or $ui.mark.step -ne $Id
	if ($fresh) { Invoke-BenchSelect $M $Id } else { Invoke-BenchShow $M $Id }
	$t0 = & $M.io.now; $dl = $t0.AddSeconds($to)
	$nc = [guid]::NewGuid().ToString('N').Substring(0, 8)
	$ui.auto = @{ step = $Id; deadline = $dl; timeout = $to; queue = @($fm); nonce = $nc; first = $true; exit = '0' }
	$a.result = ''; $a.judge = ''; $a.pending = $dl.ToString('o')   # ust review M7: nothing stale stays as the answer
	$sn = "auto: started $($t0.ToString('HH:mm:ss')), deadline $($dl.ToString('HH:mm:ss'))"
	$a.note = ([string]$a.note + "`r`n" + $sn).TrimStart()
	if ($ui.cur -eq $Id) { & $M.io.noteSet $a.note }
	& $M.io.stop $true   # ust review N2: Stop ends a waiting run
	& $M.io.save
	Invoke-BenchAutoSend $M
}

# The next block of the auto run, in runbook order; the first clears the old result and writes the begin marker
# (H1, C1); popped only once its job started (ust review N3).
function Invoke-BenchAutoSend {
	param($M)
	$au = $M.ui.auto; $b = @($au.queue)[0]; $id = $au.step
	$ca = @{ Kind = $b.kind; Text = $b.text; RunDir = $M.RunDir; Acad = $M.Acad; Main = $M.Main; IdleSec = $au.timeout }
	$ca.StepId = $id; $ca.LaneId = [string](Get-BenchModelStep $M $id).group
	if ($au.first) {
		$ca.Clear = "$($M.OutDir)/out/$id.result"; $ca.Begin = Get-BenchBeginLine -Step $id -Nonce $au.nonce
	}
	$j = Invoke-BenchRunBlock $M -Code (ConvertTo-BenchActionScript @ca) -Echo $b.text -StepId $id
	if (-not $j) { return }
	$au.first = $false; $au.queue = @($au.queue | Select-Object -Skip 1)
}

# Every 0.5 s while an auto run waits and no job runs (plan 30 S12).
function Invoke-BenchAutoTick {
	param($M)
	if ($M.ui.auto -and -not $M.ui.job) { Invoke-BenchAutoEnd $M }
}

# END seen and settled, a failed send, or the deadline: the verdict sets the answer (D2), then the lane goes on.
function Invoke-BenchAutoEnd {
	param($M)
	$au = $M.ui.auto
	try { Invoke-BenchAutoFinish $M } catch {
		$a = Get-BenchAnswer $M $au.step; $a.result = 'blocked'; $a.pending = ''; $a.judge = ''
		$a.note = ([string]$a.note + "`r`nauto: BLOCKED $($_.Exception.Message)").TrimStart()
		$M.ui.auto = $null; $M.ui.lane = @(); & $M.io.stop ([bool]$M.ui.job); & $M.io.save; & $M.io.refresh
	}
}

function Invoke-BenchAutoFinish {
	param($M)
	$ui = $M.ui; $au = $ui.auto; $now = & $M.io.now
	$late = $now -gt $au.deadline
	if ($au.exit -eq '0' -and @($au.queue).Count -and -not $late) { Invoke-BenchAutoSend $M; return }
	$id = $au.step; & $M.io.cutAcad
	$od = "$($M.OutDir)/out"
	$x = Select-BenchRunText -Text (Get-BenchStepText -Dir $od -Id $id) -Step $id -Nonce $au.nonce   # H1: this run only
	if ($au.exit -eq '0' -and -not $late) {
		if (-not (Test-BenchEndSeen -Text $x -Step $id)) { return }
		if (-not $au.endAt) { $au.endAt = $now; return }   # settle: END must still hold a second later
		if (($now - $au.endAt).TotalSeconds -lt 1) { return }
	}
	$bk = @(Get-BenchPassBlock -RunDir $M.RunDir -Stamp $M.Stamp -Touched $true)
	$ga = @{ Text = $x; Step = $id; TimedOut = $late; Block = $bk; Timeout = $au.timeout; Unsent = @($au.queue).Count }
	$ar = Get-BenchAutoResult @ga -SendExit $au.exit -SendLine ([string]$au.line)
	$a = Get-BenchAnswer $M $id
	$a.result = $ar.result; $a.benchwhy = $ar.why; $a.at = $now.ToString('o'); $a.pending = ''
	$a.note = ([string]$a.note + "`r`nauto: $($ar.result.ToUpper()) $($ar.why)").TrimStart()
	$a.judge = Get-BenchJudgeMark $M $ar.result
	# ust review L15: the step's result file is attached as evidence
	if (Test-Path -LiteralPath "$od/$id.result") { Add-BenchAnswerFile $M -Rel "bench-run/out/$id.result" -Id $id }
	if ($ui.cur -eq $id) { & $M.io.noteSet $a.note }   # ust review M8
	$ui.auto = $null; & $M.io.stop ([bool]$ui.job); & $M.io.save; & $M.io.refresh
	if (-not @($ui.lane).Count) { return }
	$types = @{}; foreach ($t in $M.live) { $types[$t.id] = [string]$t.type }
	$ln = Get-BenchLaneNext -Order $ui.lane -Types $types -State $M.State -Current $id
	if (-not $ln.next) { & $M.io.out $ln.why; $ui.lane = @(); return }
	Invoke-BenchAutoRun $M $ln.next
}

# Alt+L: every auto step of the open step's lane, in runbook order, one after the other.
function Invoke-BenchLaneRun {
	param($M)
	$ui = $M.ui
	if ($ui.auto) { & $M.io.out "auto run of $($ui.auto.step) is still waiting; press Stop to end it first"; return }
	$c = Get-BenchModelStep $M $ui.cur
	$ln = @($M.live | Where-Object { $c -and $_.group -eq $c.group })
	$ids = @($ln | Where-Object { [string]$_.type -eq 'auto' } | ForEach-Object { $_.id })
	if (-not $ids.Count) { & $M.io.out 'No auto steps in this lane.'; return }
	$ui.lane = @($ln | ForEach-Object { $_.id })   # every live step: Get-BenchLaneNext stops at one that needs you
	Invoke-BenchAutoRun $M $ids[0]
}

# Alt+A / Alt+L. -> $true when the key was one of them.
function Invoke-BenchKeyRun {
	param($M, [string]$Key)
	if (-not $M.ui.cur -or $Key -notin 'A', 'L') { return $false }
	if ($Key -eq 'A') { Invoke-BenchAutoRun $M $M.ui.cur } else { Invoke-BenchLaneRun $M }
	return $true
}

# A job ended: its log and new files go to its step, the exit code into the note, then the follow-up (ui.after, a
# function name called with $M, the job and the code), a failed send of an auto run, and the checks.
function Invoke-BenchJobEnd {
	param($M)
	$ui = $M.ui; $j = $ui.job; $ui.job = $null
	$code = if (Test-Path -LiteralPath $j.exit) { ([IO.File]::ReadAllText($j.exit)).Trim() } else { 'stopped' }
	# job start is UTC
	if ($code -eq '0' -and $j.start) {
		Add-BenchDuration -Main $M.Main -Step $j.step -Seconds ((Get-Date).ToUniversalTime() - $j.start).TotalSeconds
	}
	$rel = 'bench-run/out/' + [IO.Path]::GetFileName($j.log)
	Add-BenchAnswerFile $M -Rel $rel -Id $j.step
	foreach ($f in @(Get-BenchNewFiles -Root $M.RunDir -Since $j.start -Skip $M.tracked)) {
		Add-BenchAnswerFile $M -Rel $f -Id $j.step
	}
	$a = Get-BenchAnswer $M $j.step
	$a.note = (([string]$a.note).TrimEnd() + "`r`nRun $($j.n): exit $code, log $rel").TrimStart(); & $M.io.save
	if ($j.step -eq $ui.cur) { & $M.io.noteSet $a.note }
	& $M.io.head "Output: $($j.step) run $($j.n) (exit $code)"
	if ($ui.after) { $af = $ui.after; $ui.after = $null; & $af $M $j $code }   # a follow-up (S8 restart)
	# ust review H3b: a failed send fails the run
	if ($ui.auto -and $ui.auto.step -eq $j.step -and $code -ne '0') {
		$fl = @(Get-Content -LiteralPath $j.log -ErrorAction SilentlyContinue | Where-Object { $_ -like 'FAILED:*' })
		$ui.auto.exit = $code; $ui.auto.line = [string]@($fl)[-1]
	}
	& $M.io.stop ([bool]($ui.job -or $ui.auto))
	Invoke-BenchCheck $M $j.step
}

# Stop: the job is killed; a waiting auto run ends as FAIL and its lane is cleared.
function Invoke-BenchStop {
	param($M)
	$ui = $M.ui
	if ($ui.job) { Stop-BenchStepRun $ui.job }
	# a report= step being waited for keeps what matched so far (ust C8)
	$cs = if ($ui.cur) { Get-BenchModelStep $M $ui.cur } else { $null }
	if ($cs -and $cs.report) { $ui.repStop = [string]$ui.cur; Invoke-BenchCheck $M $ui.cur }
	if (-not $ui.auto) { return }
	$a = Get-BenchAnswer $M $ui.auto.step; $a.result = 'fail'; $a.pending = ''; $a.judge = ''
	$a.note = ([string]$a.note + "`r`nauto: FAIL stopped by the owner").TrimStart()
	$ui.auto = $null; $ui.lane = @(); & $M.io.stop ([bool]$ui.job); & $M.io.save; & $M.io.refresh
}

# ust review M7: closing while an auto run waits asks first; closed anyway, it is FAIL at the next open.
function Test-BenchCloseOk {
	param($M)
	if (-not $M.ui.auto) { return $true }
	$q = "The auto run of $($M.ui.auto.step) is still waiting. Close anyway (it becomes FAIL)?"
	return [bool](& $M.io.confirm $q 'Close')
}

# Window open: a run the last window left waiting is FAIL now (ust review M7, N5), saved at once.
function Invoke-BenchWindowOpen {
	param($M)
	$ch = @(Close-BenchPendingRun -State $M.State)
	& $M.io.save
	return $ch
}

# Restart AutoCAD (plan 30 S8 / D1): list unsaved drawings in a job, the owner confirms, quit in a job, then start.
function Invoke-BenchRestart {
	param($M)
	$ui = $M.ui
	# ust review N7: never under a waiting auto run
	if (-not $ui.cur -or $ui.job -or $ui.auto) {
		& $M.io.msg 'Open a step with nothing running first.' 'Restart AutoCAD'; return
	}
	$sc = ConvertTo-BenchActionScript -Kind 'acad-unsaved' -Text '' -RunDir $M.RunDir
	if (Invoke-BenchRunBlock $M -Code $sc -Echo 'list unsaved drawings') { $ui.after = 'Invoke-BenchRestartAsk' }
}

function Invoke-BenchRestartAsk {
	param($M, $Job, [string]$Code)
	# never a local $m: names are case-blind, it would hide the model
	$rk = Get-BenchRestartAsk -Lines @(Get-Content -LiteralPath $Job.log -ErrorAction SilentlyContinue) -Code $Code
	if (-not $rk.ok) { & $M.io.msg "Restart stopped: $($rk.why)" 'Restart AutoCAD'; return }
	if (-not (& $M.io.confirm $rk.ask 'Restart AutoCAD')) { return }
	$st = Read-BenchAcadStatus "$($M.RunDir)/bench-run/acad-status.txt"
	$sc = ConvertTo-BenchActionScript -Kind 'acad-quit' -Text ([string]$st.hwnd) -RunDir $M.RunDir
	if (Invoke-BenchRunBlock $M -Code $sc -Echo 'quit AutoCAD') { $M.ui.after = 'Invoke-BenchRestartGo' }
}

function Invoke-BenchRestartGo {
	param($M, $Job, [string]$Code)
	if ($Code -ne '0') {
		$fl = @(Get-Content -LiteralPath $Job.log -ErrorAction SilentlyContinue | Where-Object { $_ -like 'FAILED:*' })
		& $M.io.msg "Restart stopped: $(@($fl)[-1])" 'Restart AutoCAD'; return
	}
	Invoke-BenchAcadStart $M
}

# The Uncompiled sources toggle: write the mode, recheck rebuild-first (compiled mode may need it again).
function Invoke-BenchLoadModeClick {
	param($M, [bool]$On)
	$m = if ($On) { 'lsp' } else { 'vlx' }
	Write-BenchLoadMode -RunDir $M.RunDir -Mode $m -Lsp $M.Lsp; $M.ui.vlxSig = $null
	[void](Invoke-BenchRebuildRecheck -RunDir $M.RunDir -Vlx $M.Vlx -Stamp $M.Stamp)
	if (Get-Process -Name acad -ErrorAction SilentlyContinue) {
		& $M.io.out "Load mode is now $m. Restart AutoCAD: the running one keeps what it loaded."
	}
}

# Start AutoCAD (rebuild bar, restart): a start-acad job under the open step.
function Invoke-BenchAcadStart {
	param($M)
	[void](Invoke-BenchRebuildRecheck -RunDir $M.RunDir -Vlx $M.Vlx -Stamp $M.Stamp)
	$sc = ''
	$sa = @{ Kind = 'start-acad'; Text = ''; RunDir = $M.RunDir; Acad = $M.Acad; Main = $M.Main }
	$at = ' (Start AutoCAD button of the rebuild bar or restart' + $(if ($M.ui.cur) { ", step $($M.ui.cur))" } else { ')' })
	try { $sc = ConvertTo-BenchActionScript @sa }
	catch { & $M.io.out "Cannot start AutoCAD${at}: $($_.Exception.Message)" }
	if ($sc -and $M.ui.cur) { [void](Invoke-BenchRunBlock $M -Code $sc) }
	elseif ($sc) { & $M.io.out 'Open a step first: Start AutoCAD runs under it.' }
}

# AutoCAD lines since the step was opened go to <step>-acad.log (attached), each visit its own section (plan 30 S5).
function Invoke-BenchCutAcad {
	param($M)
	$ui = $M.ui; $mk = $ui.mark
	if (-not $mk) { return }
	$sl = Get-BenchAcadLogSlice -Dir $M.acadDir -Sizes $mk.sizes; $mk.sizes = $sl.sizes
	if (-not $sl.text.Trim()) { return }
	New-Item -ItemType Directory -Path "$($M.OutDir)/out" -Force | Out-Null
	$lf = "$($M.OutDir)/out/$($mk.step)-acad.log"
	$txt = Get-BenchSliceText -Text $sl.text -Head ([bool]$mk.head) -Opened $ui.since -TailLf (Test-BenchTailLf $lf)
	$mk.head = $false
	[IO.File]::AppendAllText($lf, $txt)
	Add-BenchAnswerFile $M -Rel "bench-run/out/$($mk.step)-acad.log" -Id $mk.step
	if ($mk.step -eq $ui.cur -and -not $ui.job) { & $M.io.pane $ui.cur }
	& $M.io.errShow $mk.step
	Invoke-BenchCheck $M $mk.step
}

# AutoCAD error lines of the step's last visit, kept in its answer (RESULT.tsv note) -> the lines (ust 4ad063b #13).
function Invoke-BenchAcadError {
	param($M, [string]$Id)
	$lf = "$($M.OutDir)/out/$Id-acad.log"
	$lv = if (Test-Path -LiteralPath $lf) { Get-BenchLastVisit (Read-BenchLogTail -Path $lf -Offset 0).text }
	$lines = @(if ($lv) { Get-BenchErrorLines $lv })
	if ($lines.Count -or $M.State.answers[$Id]) {
		# compared as text: @($null).Count is 1, so a first single error line once read as unchanged
		$a = Get-BenchAnswer $M $Id; $was = @($a.acaderr | Where-Object { $null -ne $_ }) -join "`n"
		if ($was -ne ($lines -join "`n")) { $a.acaderr = $lines; & $M.io.save }
	}
	return $lines
}

# The window's keys (pure, ust review 4ad063b #1) -> @{ act = go | paste | answer | run; arg }, or $null.
# Ctrl+Enter next unanswered, Ctrl+V paste (not in a text box), Alt+Left/Right move, Alt+P/F/B/N answer, Alt+A/L run.
function Get-BenchKeyAction {
	param([string]$Key, [string]$Mods, [bool]$Steps, [bool]$TextFocus)
	if (-not $Steps) { return $null }
	$alt = $Mods -match '\bAlt\b'; $ctrl = $Mods -match '\bControl\b'
	if ($ctrl -and $Key -eq 'Return') { return @{ act = 'go'; arg = 0 } }
	if ($ctrl -and $Key -eq 'V' -and -not $TextFocus) { return @{ act = 'paste'; arg = $null } }
	if (-not $alt -or $ctrl) { return $null }
	if ($Key -eq 'Left') { return @{ act = 'go'; arg = -1 } }
	if ($Key -eq 'Right') { return @{ act = 'go'; arg = 1 } }
	$ak = @{ P = 'pass'; F = 'fail'; B = 'blocked'; N = 'na' }[$Key]
	if ($ak) { return @{ act = 'answer'; arg = $ak } }
	if ($Key -in 'A', 'L') { return @{ act = 'run'; arg = $Key } }
	return $null
}

# --- WPF runbook window (plan 20; Windows only, proved on the owner's run) ----

function Show-RunbookWindow {
	param([string]$Title, $Rb, $State, [string]$OutDir, [string]$RunDir = '', [string]$Exe = 'powershell.exe', [scriptblock]$PushPlan = { @{ cand = @(); strays = @(); refused = @() } },
		[System.Collections.ArrayList]$Picked = (New-Object System.Collections.ArrayList), [datetime]$Since = (Get-Date),
		[string]$Acad = '', [string]$Main = '', [string]$RunId = '', [string[]]$Vlx = @(), [string]$Stamp = '',
		[string[]]$ClearEnv = @(), [string[]]$Lsp = @())
	if ([Threading.Thread]::CurrentThread.GetApartmentState() -ne 'STA') { throw 'The runbook window needs an STA thread: run git-sp with powershell.exe, or pwsh -STA.' }
	Add-Type -AssemblyName PresentationFramework, PresentationCore, WindowsBase, System.Xaml, System.Windows.Forms, System.Drawing, Microsoft.VisualBasic
	$W = 'System.Windows'
	$statePath = "$OutDir/results.json"
	if (-not $RunDir) { $RunDir = Split-Path -Parent $OutDir }
	$steps = @($Rb.steps)
	$live = @($steps | Where-Object { -not $_.hidden })   # settled steps do not count as open
	$ui = @{ cur = $null; exit = ''; load = $false; reveal = $null; exp = (New-Object 'System.Collections.Generic.HashSet[string]'); job = $null; off = 0 }
	$doneRoot = 'Tester responded'
	$colour = @{ open = 'White'; pass = 'ForestGreen'; fail = 'Firebrick'; na = 'Black'; blocked = 'DarkOrange' }

	$xaml = @'
<Window xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        Width="1200" Height="820" WindowStartupLocation="CenterScreen" FontFamily="Segoe UI" FontSize="13">
  <DockPanel>
    <DockPanel DockPanel.Dock="Top" Margin="6,4">
      <TextBlock x:Name="Prog" VerticalAlignment="Center" Margin="0,0,12,0"/>
      <ComboBox x:Name="Filter" Width="130" SelectedIndex="0"><ComboBoxItem Content="all"/><ComboBoxItem Content="not answered"/><ComboBoxItem Content="failed"/></ComboBox>
      <CheckBox x:Name="OnTop" Content="Always on top" Margin="12,0" VerticalAlignment="Center"/>
      <CheckBox x:Name="Uncompiled" Content="Uncompiled sources" Margin="12,0" VerticalAlignment="Center"
                Visibility="Collapsed"
                ToolTip="Load the .lsp sources ([bench] lsp =) instead of the VLX; next AutoCAD start"/>
      <TextBlock Foreground="Gray" VerticalAlignment="Center" Text="Alt+P/F/B/N mark   Alt+Left/Right prev/next   Ctrl+Enter next unanswered   Ctrl+V paste image"/>
    </DockPanel>
    <!-- status bar: two lines (AutoCAD state; build and run folder), buttons on their own row (owner 2026-11-09) -->
    <DockPanel DockPanel.Dock="Bottom" Margin="4">
      <StackPanel DockPanel.Dock="Bottom" Orientation="Horizontal" HorizontalAlignment="Right" Margin="0,4,0,0">
        <Button x:Name="Abort" Content="Abort run" Margin="4,0" Padding="12,3"/>
        <Button x:Name="Finish" Content="Finish and push" Margin="4,0" Padding="12,3" FontWeight="Bold"/>
      </StackPanel>
      <TextBlock x:Name="AcadStatus" DockPanel.Dock="Top" Margin="4,0" Text="AutoCAD: ?"
                 TextTrimming="CharacterEllipsis"/>
      <DockPanel>
        <TextBlock x:Name="VlxInfo" Margin="4,0" VerticalAlignment="Center"/>
        <TextBlock x:Name="RunInfo" Margin="16,0" VerticalAlignment="Center" Foreground="Gray"
                   TextTrimming="CharacterEllipsis"/>
      </DockPanel>
    </DockPanel>
    <Border x:Name="Alarm" DockPanel.Dock="Top" Background="#FFC62828" Visibility="Collapsed" Padding="8,4">
      <DockPanel>
        <Button x:Name="RestartAcad" DockPanel.Dock="Right" Content="Restart AutoCAD" Margin="4,0" Padding="12,3"
                Visibility="Collapsed"/>
        <TextBlock x:Name="AlarmText" Foreground="White" FontWeight="Bold" TextWrapping="Wrap"/>
      </DockPanel>
    </Border>
    <Border x:Name="Rebuild" DockPanel.Dock="Top" Background="#FFFFF3CD" Visibility="Collapsed" Padding="8,4">
      <TextBlock x:Name="RebuildText" TextWrapping="Wrap"/>
    </Border>
    <TabControl x:Name="Tabs">
      <TabItem Header="Steps" x:Name="TabSteps">
        <Grid>
          <Grid.ColumnDefinitions><ColumnDefinition Width="210" MinWidth="80"/><ColumnDefinition Width="5"/><ColumnDefinition Width="*"/></Grid.ColumnDefinitions>
          <TreeView x:Name="Tree" Grid.Column="0"/>
          <GridSplitter Grid.Column="1" Width="5" HorizontalAlignment="Stretch" ResizeBehavior="PreviousAndNext"/>
          <Grid Grid.Column="2">
            <Grid.RowDefinitions>
              <RowDefinition Height="Auto"/><RowDefinition Height="*" MinHeight="80"/><RowDefinition Height="5"/>
              <RowDefinition Height="220" MinHeight="60"/>
            </Grid.RowDefinitions>
            <ToolBarTray Grid.Row="0" IsLocked="True"><ToolBar x:Name="Tool"/></ToolBarTray>
            <DockPanel Grid.Row="1">
              <Border x:Name="StateBox" DockPanel.Dock="Top" Background="LightYellow" Padding="6" Visibility="Collapsed">
                <TextBlock x:Name="StateLbl" FontWeight="Bold" TextWrapping="Wrap"/>
              </Border>
              <Border x:Name="CheckBox_" DockPanel.Dock="Top" Padding="6,3" Visibility="Collapsed">
                <TextBlock x:Name="CheckLbl" TextWrapping="Wrap"/>
              </Border>
              <FlowDocumentScrollViewer x:Name="Doc" VerticalScrollBarVisibility="Auto"/>
            </DockPanel>
            <GridSplitter Grid.Row="2" Height="5" HorizontalAlignment="Stretch" ResizeBehavior="PreviousAndNext"/>
            <!-- Notes and Output share one tab view (owner 2026-11-09); Stop and progress sit on the tab strip -->
            <Grid Grid.Row="3">
              <TabControl x:Name="NoteTabs">
                <TabItem x:Name="NoteTab" Header="Notes">
                  <DockPanel>
                    <DockPanel x:Name="ErrBar" DockPanel.Dock="Bottom" Visibility="Collapsed">
                      <Button x:Name="ErrIns" DockPanel.Dock="Right" Content="Insert into note" Padding="8,0" Margin="2"/>
                      <TextBlock x:Name="ErrLbl" Margin="4,2" Foreground="Firebrick" FontWeight="Bold"
                                 VerticalAlignment="Center" TextTrimming="CharacterEllipsis"/>
                    </DockPanel>
                    <TextBox x:Name="Note" AcceptsReturn="True" TextWrapping="Wrap" VerticalScrollBarVisibility="Auto"/>
                  </DockPanel>
                </TabItem>
                <TabItem x:Name="OutTab" Header="Output">
                  <DockPanel>
                    <TextBlock x:Name="OutHead" DockPanel.Dock="Top" Margin="4,2" Text="Output" FontWeight="Bold"/>
                    <TextBox x:Name="Out" IsReadOnly="True" FontFamily="Consolas" FontSize="12"
                             VerticalScrollBarVisibility="Auto" HorizontalScrollBarVisibility="Auto"/>
                  </DockPanel>
                </TabItem>
              </TabControl>
              <StackPanel Orientation="Horizontal" HorizontalAlignment="Right" VerticalAlignment="Top">
                <ProgressBar x:Name="JobProg" Width="180" Height="12" Margin="4,4" Visibility="Collapsed"/>
                <TextBlock x:Name="JobProgText" Margin="6,2" Foreground="Gray" VerticalAlignment="Center"/>
                <Button x:Name="Stop" Content="Stop" IsEnabled="False" Padding="10,0" Margin="2"/>
              </StackPanel>
            </Grid>
          </Grid>
        </Grid>
      </TabItem>
      <TabItem Header="Files" x:Name="TabFiles">
        <DockPanel>
          <TextBlock DockPanel.Dock="Top" Margin="6" Foreground="DimGray" Text="Files new or changed in the run folder since the run started. Each is attached to the step that was open when it was written."/>
          <ListView x:Name="FileList">
            <ListView.View><GridView>
              <GridViewColumn Header="Step" Width="80" DisplayMemberBinding="{Binding Step}"/>
              <GridViewColumn Header="File" Width="560" DisplayMemberBinding="{Binding File}"/>
              <GridViewColumn Header="KB" Width="70" DisplayMemberBinding="{Binding KB}"/>
              <GridViewColumn Header="Written" Width="90" DisplayMemberBinding="{Binding Time}"/>
            </GridView></ListView.View>
          </ListView>
        </DockPanel>
      </TabItem>
      <TabItem Header="General comments"><TextBox x:Name="Gen" AcceptsReturn="True" TextWrapping="Wrap" VerticalScrollBarVisibility="Auto"/></TabItem>
      <TabItem Header="Review and push" x:Name="TabReview">
        <DockPanel>
          <StackPanel DockPanel.Dock="Bottom" Orientation="Horizontal" HorizontalAlignment="Right" Margin="6">
            <Button x:Name="Back" Content="Back to steps" Margin="4,0" Padding="12,3"/>
            <Button x:Name="Push" Content="Push ticked files" Margin="4,0" Padding="12,3" FontWeight="Bold"/>
          </StackPanel>
          <TextBlock x:Name="ReviewHead" DockPanel.Dock="Top" Margin="6" TextWrapping="Wrap"/>
          <TextBlock x:Name="ReviewWarn" DockPanel.Dock="Top" Margin="6,0,6,6" TextWrapping="Wrap" Foreground="Firebrick"/>
          <ListBox x:Name="ReviewList"/>
        </DockPanel>
      </TabItem>
    </TabControl>
  </DockPanel>
</Window>
'@
	$form = [Windows.Markup.XamlReader]::Parse($xaml)
	$el = @{}; foreach ($n in 'Prog', 'Filter', 'OnTop', 'Abort', 'Finish', 'AcadStatus', 'VlxInfo', 'ErrBar', 'ErrIns', 'ErrLbl', 'RunInfo', 'Alarm', 'AlarmText', 'Rebuild', 'RebuildText', 'Tabs', 'TabSteps', 'TabFiles', 'TabReview', 'Tree', 'Tool', 'Note', 'StateBox', 'StateLbl', 'CheckBox_', 'CheckLbl', 'Doc', 'Stop', 'JobProg', 'JobProgText', 'NoteTabs', 'NoteTab', 'OutTab', 'OutHead', 'Out', 'FileList', 'Gen', 'Back', 'Push', 'ReviewHead', 'ReviewWarn', 'ReviewList') { $el[$n] = $form.FindName($n) }
	$form.Title = $Title; $el.Gen.Text = $State.general; $el.RunInfo.Text = Get-BenchHeader -RunDir $RunDir -Main $Main
	$pl = "$RunDir/bench-run/prepare.log"
	if (Test-Path -LiteralPath $pl) { $last = @(Get-Content -LiteralPath $pl | Where-Object { $_ -match '\S' } | Select-Object -Last 2) -join '  |  '; $el.RunInfo.Text = (Get-BenchHeader -RunDir $RunDir -Main $Main) + "   prepare: $last"; if ($last -notmatch 'exit 0 ') { $el.RunInfo.Foreground = [Windows.Media.Brushes]::Firebrick } }
	$el.TabReview.Visibility = 'Collapsed'
	$brush = { param($c) New-Object "$W.Media.SolidColorBrush" ([Windows.Media.ColorConverter]::ConvertFromString($c)) }

	$mark = {   # 12 px status shape: circle, or orange square for blocked
		param($kind)
		if (-not $kind -or -not $colour[$kind]) { return $null }
		$sh = if ($kind -eq 'blocked') { New-Object "$W.Shapes.Rectangle" } else { New-Object "$W.Shapes.Ellipse" }
		$sh.Width = 12; $sh.Height = 12; $sh.Fill = & $brush $colour[$kind]; $sh.Stroke = & $brush 'Gray'; $sh.Margin = '0,0,5,0'; $sh
	}
	$head = {   # tree / toolbar content: optional mark + text
		param($kind, $text)
		$sp = New-Object "$W.Controls.StackPanel"; $sp.Orientation = 'Horizontal'
		$m = & $mark $kind; if ($m) { [void]$sp.Children.Add($m) }
		$t = New-Object "$W.Controls.TextBlock"; $t.Text = $text; [void]$sp.Children.Add($t); $sp
	}
	$tb = {   # toolbar button: a status mark, or a Segoe MDL2 glyph
		param($kind, $glyph, $tip, $on, $name)
		$b = New-Object "$W.Controls.Button"; $b.ToolTip = $tip; $b.Margin = '1'; $b.Padding = '4,2'
		if ($name) { $el[$name] = $b }   # a button the tick enables and disables
		if ($glyph) { $t = New-Object "$W.Controls.TextBlock"; $t.FontFamily = 'Segoe MDL2 Assets'; $t.FontSize = 15; $t.Text = [string][char]$glyph; $b.Content = $t }
		else { $b.Content = & $mark $kind }
		$b.Add_Click($on); [void]$el.Tool.Items.Add($b)
	}

	$save = { $State.general = $el.Gen.Text; Save-RunState -Path $statePath -State $State }
	$res = { param($id) if ($State.answers[$id]) { [string]$State.answers[$id].result } else { '' } }
	$fileDir = { $d = "$OutDir/files"; New-Item -ItemType Directory -Path $d -Force | Out-Null; $d }
	$ui.touched = @{}; $ui.auto = $null; $ui.lane = @(); $ui.part = ''; $ui.after = $null; $ui.repAt = [datetime]::MinValue
	$ui.laneSince = @{}
	# the window model: every handler below is one call into the Invoke-Bench* functions (ust review: testable)
	$M = @{ State = $State; steps = $steps; live = $live; Rb = $Rb; RunDir = $RunDir; OutDir = $OutDir; ui = $ui }
	$M.Stamp = $Stamp; $M.Acad = $Acad; $M.Main = $Main; $M.Exe = $Exe; $M.Vlx = $Vlx; $M.tracked = @{}; $M.Lsp = $Lsp
	$M.acadDir = "$RunDir/logs/acad"; $M.Since = $Since

	# --- runbook: blocks -> FlowDocument, code blocks with Copy / Run ---
	$openPath = {   # F3/F5: resolved when clicked (a later step may make the file); drawings open in the running AutoCAD
		param($t)
		$p = Resolve-BenchPath $t $RunDir
		$say = { param($m) if (-not $ui.job) { $el.Out.AppendText("$m`r`n"); $el.Out.ScrollToEnd() } }
		if (-not (Test-Path -LiteralPath $p)) { & $say "not found: $p"; return }
		if (Test-Path -LiteralPath $p -PathType Container) { Start-Process explorer.exe "`"$p`""; & $say "opened folder: $p"; return }
		if ($p -match '\.(dwg|dxf)$' -and $ui.cur -and -not $ui.job) {
			Invoke-BenchActionRun $M -Kind open -Text $p; return
		}
		Start-Process -FilePath $p; & $say "opened: $p"
	}
	$inlines = {
		param($para, [string]$text)
		foreach ($t in (Get-MdInlines $text)) {
			$run = New-Object "$W.Documents.Run" $t.t
			switch ($t.k) {
				'code' {
					$run.FontFamily = 'Consolas'; $run.Background = & $brush '#FFEFEFEF'
					if (Test-BenchPathLike $t.t) { $h = New-Object "$W.Documents.Hyperlink" $run; $h.Tag = $t.t; $h.ToolTip = "Open $(Resolve-BenchPath $t.t $RunDir)"; $h.Add_Click({ & $openPath $this.Tag }); [void]$para.Inlines.Add($h) }
					else { [void]$para.Inlines.Add($run) }
				}
				'bold' { [void]$para.Inlines.Add((New-Object "$W.Documents.Bold" $run)) }
				'italic' { [void]$para.Inlines.Add((New-Object "$W.Documents.Italic" $run)) }
				'link' {
					$h = New-Object "$W.Documents.Hyperlink" $run; $h.Tag = $t.url
					$h.Add_Click({ $u = [string]$this.Tag; if ($u -match '^https?://') { Start-Process $u } else { & $openPath $u } })
					[void]$para.Inlines.Add($h)
				}
				default { [void]$para.Inlines.Add($run) }
			}
		}
	}
	$codeBlock = {
		param($seg)
		$bd = New-Object "$W.Controls.Border"; $bd.BorderBrush = & $brush 'Silver'; $bd.BorderThickness = '1'; $bd.Background = & $brush '#FFF7F7F7'; $bd.Margin = '0,4,0,8'
		$dp = New-Object "$W.Controls.DockPanel"
		$bar = New-Object "$W.Controls.StackPanel"; $bar.Orientation = 'Horizontal'; [Windows.Controls.DockPanel]::SetDock($bar, 'Top')
		$lbl = New-Object "$W.Controls.TextBlock"; $lbl.Text = $(if ($seg.lang) { $seg.lang } else { 'text' }); $lbl.Foreground = & $brush 'Gray'; $lbl.Margin = '6,2'; [void]$bar.Children.Add($lbl)
		$cp = New-Object "$W.Controls.Button"; $cp.Content = 'Copy'; $cp.Padding = '8,0'; $cp.Margin = '2'; $cp.Tag = $seg.text
		$cp.Add_Click({ try { [Windows.Clipboard]::SetDataObject([string]$this.Tag, $true) } catch { [Windows.MessageBox]::Show("The clipboard is busy: $_", 'Copy') | Out-Null } }); [void]$bar.Children.Add($cp)
		if ($seg.run -and $ui.cur) {   # lane text: Copy only (Run attaches to a step)
			$rn = New-Object "$W.Controls.Button"; $rn.Content = 'Run'; $rn.Padding = '8,0'; $rn.Margin = '2'; $rn.FontWeight = 'Bold'; $rn.Tag = $seg.text
			$rn.ToolTip = "Runs in $RunDir with Windows PowerShell; output below, log attached to the step"
			$rn.Add_Click({ [void](Invoke-BenchRunBlock $M -Code ([string]$this.Tag)) }); [void]$bar.Children.Add($rn)
		}
		if ($seg.act -and $ui.cur) {   # action fences (F4): a generated script through the same Run machinery (output, log, exit code)
			$label = @{ lisp = 'Send to AutoCAD'; acad = 'Send to AutoCAD'; open = 'Open'; 'start-acad' = 'Start AutoCAD' }[$seg.act]
			$rn = New-Object "$W.Controls.Button"; $rn.Content = $label; $rn.Padding = '8,0'; $rn.Margin = '2'; $rn.FontWeight = 'Bold'; $rn.Tag = @($seg.act, $seg.text)
			$rn.ToolTip = @{ lisp = 'Sends each form to the running AutoCAD (COM SendCommand)'; acad = 'Sends each line to the running AutoCAD command line'; open = 'Opens each path: drawings in the running AutoCAD, other files in their app'; 'start-acad' = "Starts AutoCAD$(if ($seg.text.Trim()) { ' with the command line in the block' } elseif ($Acad) { ": $Acad" } else { ' (no [bench] acad = in .bench.ini)' })" }[$seg.act] + '; output below, log attached to the step'
			$rn.Add_Click({ Invoke-BenchActionRun $M -Kind @($this.Tag)[0] -Text @($this.Tag)[1] })
			[void]$bar.Children.Add($rn)
		}
		[void]$dp.Children.Add($bar)
		$tx = New-Object "$W.Controls.TextBlock"; $tx.Text = $seg.text; $tx.FontFamily = 'Consolas'; $tx.TextWrapping = 'Wrap'; $tx.Padding = '6,2'   # not a TextBox: its ScrollViewer eats the wheel
		[void]$dp.Children.Add($tx); $bd.Child = $dp
		New-Object "$W.Documents.BlockUIContainer" $bd
	}
	$render = {
		param($obj)
		$doc = New-Object "$W.Documents.FlowDocument"; $doc.FontFamily = 'Segoe UI'; $doc.FontSize = 13; $doc.PagePadding = '10'
		$h = New-Object "$W.Documents.Paragraph"; $h.FontSize = 17; $h.FontWeight = 'Bold'; [void]$h.Inlines.Add((New-Object "$W.Documents.Run" "$($obj.id). $($obj.title)")); [void]$doc.Blocks.Add($h)
		if ($obj.type -and $obj.type -ne 'manual') { $p = New-Object "$W.Documents.Paragraph"; $p.Foreground = & $brush 'Gray'; [void]$p.Inlines.Add((New-Object "$W.Documents.Run" "type: $($obj.type)$(if ($obj.restart) { "   AutoCAD: $($obj.restart)" })")); [void]$doc.Blocks.Add($p) }
		foreach ($seg in (Get-RunbookSegments -Lines @($obj.body))) {
			if ($seg.kind -eq 'code') { [void]$doc.Blocks.Add((& $codeBlock $seg)); continue }
			foreach ($b in (Get-MdBlocks $seg.text)) {
				switch ($b.k) {
					'h' { $p = New-Object "$W.Documents.Paragraph"; $p.FontWeight = 'Bold'; $p.FontSize = [Math]::Max(13, 19 - 2 * $b.n); & $inlines $p $b.t; [void]$doc.Blocks.Add($p) }
					'p' { $p = New-Object "$W.Documents.Paragraph"; & $inlines $p $b.t; [void]$doc.Blocks.Add($p) }
					'table' {
						$t = New-Object "$W.Documents.Table"; $t.CellSpacing = 0; $t.BorderBrush = & $brush 'Silver'; $t.BorderThickness = '1'
						$g = New-Object "$W.Documents.TableRowGroup"; $first = $true
						foreach ($row in $b.rows) {
							$tr = New-Object "$W.Documents.TableRow"
							foreach ($c in @($row)) {
								$p = New-Object "$W.Documents.Paragraph"; if ($first -and $b.head) { $p.FontWeight = 'Bold' }; & $inlines $p ([string]$c)
								$cell = New-Object "$W.Documents.TableCell" $p; $cell.BorderBrush = & $brush 'Silver'; $cell.BorderThickness = '0.5'; $cell.Padding = '4,2'; [void]$tr.Cells.Add($cell)
							}
							[void]$g.Rows.Add($tr); $first = $false
						}
						[void]$t.RowGroups.Add($g); [void]$doc.Blocks.Add($t)
					}
					default {   # ul / ol
						$l = New-Object "$W.Documents.List"; $l.MarkerStyle = $(if ($b.k -eq 'ol') { 'Decimal' } else { 'Disc' })
						foreach ($it in $b.items) { $p = New-Object "$W.Documents.Paragraph"; & $inlines $p $it; [void]$l.ListItems.Add((New-Object "$W.Documents.ListItem" $p)) }
						[void]$doc.Blocks.Add($l)
					}
				}
			}
		}
		$el.Doc.Document = $doc
	}

	# --- Run buttons (plan 20 S3) ---
	$outFor = {   # newest run log of a step, or ''
		param($id)
		$f = @(Get-ChildItem -LiteralPath "$OutDir/out" -Filter "$id-*.log" -ErrorAction SilentlyContinue | Where-Object { $_.Name -match "^$([regex]::Escape($id))-\d+\.log$" } | Sort-Object LastWriteTime)
		if ($f.Count) { $f[-1].FullName } else { '' }
	}
	$ui.part = ''
	$liveOut = {   # a running step's log, formatted a whole line at a time (Format-BenchConsole)
		param([string]$chunk, [bool]$last)
		$txt = $ui.part + $chunk; $cut = $txt.LastIndexOf("`n")
		if ($last) { $cut = $txt.Length - 1 }
		if ($cut -lt 0) { $ui.part = $txt; return }
		$ui.part = $txt.Substring($cut + 1); $done = $txt.Substring(0, $cut + 1)
		if ($done.Trim()) {
			$el.Out.AppendText((Format-BenchConsole $done) + "`r`n"); $el.Out.ScrollToEnd()
			Show-BenchOutFlag -Tab $el.OutTab -Text $done
		}
	}
	# the running job's progress bar (Get-BenchJobProgress)
	$progShow = {
		$sec = if ($ui.job.start) { ((Get-Date).ToUniversalTime() - $ui.job.start).TotalSeconds } else { 0 }
		$pa = @{ Text = $ui.jobText; Step = $ui.job.step; Elapsed = $sec; LastSec = [double]$ui.jobLast }
		$pg = Get-BenchJobProgress @pa
		$el.JobProg.Visibility = 'Visible'; $el.JobProg.IsIndeterminate = ($pg.pct -lt 0)
		if ($pg.pct -ge 0) { $el.JobProg.Value = $pg.pct }
		$el.JobProgText.Text = "$($ui.job.step): $($pg.text)"
	}
	$jobTick = {   # a running job: new log lines to the pane; at its exit its last lines, then the job ends
		if (-not $ui.job) { return }
		$t = Read-BenchLogTail -Path $ui.job.log -Offset $ui.off; $ui.off = $t.offset
		if ($t.text -and $ui.cur -eq $ui.job.step) { & $liveOut $t.text $false }
		$ui.jobText = [string]$ui.jobText + [string]$t.text
		if (-not $ui.job.proc.HasExited) { & $progShow; return }
		$el.JobProg.Visibility = 'Collapsed'; $el.JobProgText.Text = ''
		$t = Read-BenchLogTail -Path $ui.job.log -Offset $ui.off; $ui.off = $t.offset
		if ($ui.cur -eq $ui.job.step) { & $liveOut $t.text $true }
		Invoke-BenchJobEnd $M
	}
	$tickErr = { param($e) $el.AlarmText.Text = "window error (the run goes on): $e"; $el.Alarm.Visibility = 'Visible' }
	$timer = New-Object "$W.Threading.DispatcherTimer"; $timer.Interval = [TimeSpan]::FromMilliseconds(500)
	$timer.Add_Tick({ try { & $jobTick; & $tick } catch { & $tickErr $_ } })
	$el.Stop.Add_Click({ Invoke-BenchStop $M })
	$rbDone = {
		$on = [bool](Get-Process -Name acad -ErrorAction SilentlyContinue)
		$rm = Complete-BenchRebuild -RunDir $RunDir -Vlx $Vlx -Stamp $Stamp -Running $on
		if ($rm) { [void][Windows.MessageBox]::Show($rm, 'Rebuild done') }
	}
	$recheck = { [void](Invoke-BenchRebuildRecheck -RunDir $RunDir -Vlx $Vlx -Stamp $Stamp) }
	# [bench] lsp = set: uncompiled is the default, written before the first rebuild check (ust R20261109-0735)
	if ($Lsp.Count -and $RunDir -and -not (Test-Path -LiteralPath "$RunDir/bench-run/load-mode.txt")) {
		Write-BenchLoadMode -RunDir $RunDir -Mode 'lsp' -Lsp $Lsp
	}
	& $recheck
	$el.RestartAcad = $form.FindName('RestartAcad'); $el.RestartAcad.Add_Click({ Invoke-BenchRestart $M })

	# --- AutoCAD capture, state and expect checks (plan 20 S4/S5) ---
	$acadDir = "$RunDir/logs/acad"
	$ui.mark = $null; $ui.since = Get-Date; $ui.n = 0
	$acadLog = { param($id) "$OutDir/out/$id-acad.log" }
	$errShow = {   # AutoCAD error lines of a step: kept in its answer (RESULT.tsv note), one line under the note box
		param($id)
		if (-not $id) { $el.ErrBar.Visibility = 'Collapsed'; return }
		$lines = @(Invoke-BenchAcadError $M $id)
		if ($id -ne $ui.cur) { return }
		$ui.errs = $lines
		$el.ErrLbl.Text = "$($lines.Count) AutoCAD error line(s) captured (attached: $([IO.Path]::GetFullPath((& $acadLog $id)))): $($lines[0])"
		$el.ErrLbl.ToolTip = $lines -join "`n"
		$el.ErrBar.Visibility = $(if ($lines.Count) { 'Visible' } else { 'Collapsed' })
	}
	$el.ErrIns.Add_Click({ if ($ui.cur -and @($ui.errs).Count) { $el.Note.Text = ($el.Note.Text.TrimEnd() + "`r`nAutoCAD:`r`n" + (@($ui.errs) -join "`r`n")).TrimStart() } })
	$showOut = {   # output pane when nothing runs: last run log + AutoCAD lines of the step
		param($id)
		$parts = @(); $lg = & $outFor $id
		if ($lg) { $parts += Format-BenchConsole (Read-BenchLogTail -Path $lg -Offset 0).text -Summary }
		if (Test-Path -LiteralPath (& $acadLog $id)) {
			$at = Get-BenchLastVisit (Read-BenchLogTail -Path (& $acadLog $id) -Offset 0).text
			$parts += "--- AutoCAD ---`r`n" + (Format-BenchConsole $at -Summary)
		}
		$el.Out.Text = $parts -join "`r`n"; $el.OutHead.Text = $(if ($parts.Count) { "Output: $id" } else { 'Output' }); $el.Out.ScrollToEnd()
	}
	$expectShow = {   # the expect / fail box of the open step (Invoke-BenchCheck): a Test-BenchExpect result, or $null
		param($t)
		if (-not $t) { $el.CheckBox_.Visibility = 'Collapsed'; return }
		$key = @{ pass = 'Alt+P'; fail = 'Alt+F' }[$t.result]
		$msg = if ($t.result) { "Suggested: $($t.result.ToUpper()) ($key)" } else { 'No output yet to check.' }
		if ($t.missing.Count) { $msg += "`nNot found: " + ($t.missing -join '   ') }
		if ($t.hits.Count) { $msg += "`nMatched: " + ($t.hits -join "`n         ") }
		$el.CheckLbl.Text = $msg
		$bg = @{ pass = '#FFDFF2E0'; fail = '#FFF8D7D7' }[[string]$t.result]
		$el.CheckBox_.Background = & $brush $(if ($bg) { $bg } else { '#FFEFEFEF' })
		$el.CheckBox_.Visibility = 'Visible'
	}
	$tick = {   # every 2 s: AutoCAD capture for the open step, AutoCAD state, Files panel
		Invoke-BenchAutoTick $M   # plan 30 S12: every 0.5 s while an auto step waits for END
		$ui.n++; if ($ui.n % 4) { return }
		& $recheck
		Invoke-BenchCutAcad $M
		$st = Read-BenchAcadStatus "$OutDir/acad-status.txt"
		$on = [bool](Get-Process -Name acad -ErrorAction SilentlyContinue)
		$info = '   (no drawing loaded the bench yet)'
		if ($st) {
			$info = "   last load $($st.time): $($st.load), SECURELOAD $($st.secureload), bundle trusted $($st.trusted)"
			$info += ", bench session $($st.bench), support first $($st['support-first'])"
		}
		$el.AcadStatus.Text = 'AutoCAD: ' + $(if ($on) { 'running' } else { 'not running' }) + $info
		$swArgs = @{
			Contents = "$env:APPDATA/Autodesk/ApplicationPlugins/git-sp-bench.bundle/Contents"; Status = $st; Main = $Main
			RunDir = $RunDir; ClearEnv = $ClearEnv; BenchRunning = ($on -and $st -and $st.bench -eq 'yes')
		}
		$sw = @(Get-BenchStaleWarning @swArgs)
		if ($sw.Count) { $el.AcadStatus.Text += '   WARNING: ' + ($sw -join '   WARNING: ') }
		$s = $steps | Where-Object { $_.id -eq $ui.cur } | Select-Object -First 1
		$iss = @(Get-BenchStateIssues -Step $s -Running $on -Status $st -RunDir $RunDir -Since $ui.since)
		if ($on -and $ui.cur) { $ui.touched[$ui.cur] = $true }   # AutoCAD seen running while this step is open
		# report= steps: look for the report every 3 s while the step is open (the harness writes it at its end)
		if ($s -and $s.report -and ((Get-Date) - [datetime]$ui.repAt).TotalSeconds -ge 3) {
			$ui.repAt = Get-Date; Invoke-BenchCheck $M $ui.cur
		}
		if ($ui.cur) { $iss += @(Get-BenchStepJudge $M $ui.cur | Where-Object { $iss -notcontains $_ }) }
		$rf = Get-BenchRebuildState -RunDir $RunDir
		if ($rf) { $iss = @($rf.reason) + $iss }
		$el.Rebuild.Visibility = $(if ($rf) { 'Visible' } else { 'Collapsed' })
		if ($el.TbStart) { $el.TbStart.IsEnabled = -not $on -and -not $ui.job }
		if ($el.TbRebuilt) { $el.TbRebuilt.IsEnabled = [bool]$rf -and -not $on }
		$prv = @($Vlx | ForEach-Object {
				$f = Get-BenchFullPath -Dir $RunDir -Rel ([IO.Path]::ChangeExtension($_, '.prv'))
				if (Test-Path -LiteralPath $f) { $f } else { Get-BenchFullPath -Dir $RunDir -Rel $_ }
			})
		$t = "Rebuild first, in the RUN folder $([IO.Path]::GetFullPath($RunDir)) (not the main clone):"
		$t += "`n1 Start AutoCAD.`n2 MAKELISPAPP each:`n   $($prv -join "`n   ")"
		$el.RebuildText.Text = "$t`n3 Quit AutoCAD fully.`n4 Rebuild done."
		$el.AlarmText.Text = $iss -join "`n"; $el.Alarm.Visibility = $(if ($iss.Count) { 'Visible' } else { 'Collapsed' })
		$el.RestartAcad.Visibility = $(if ($iss.Count -and $on) { 'Visible' } else { 'Collapsed' })
		$sig = (@($Vlx | ForEach-Object { $f = "$RunDir/$_"; if (Test-Path -LiteralPath $f) { (Get-Item -LiteralPath $f).LastWriteTimeUtc.Ticks } else { 0 } }) -join ',')
		# uncompiled: the sources and their proof; else the VLX stamps, read again when a VLX changes
		if ($Lsp.Count -and (Get-BenchLoadMode -RunDir $RunDir) -eq 'lsp') {
			$pf = @(Get-Content -LiteralPath "$RunDir/bench-run/lsp-src.txt" -ErrorAction Ignore)
			$pst = if ($pf.Count) { $pf[0] } else { 'not checked yet' }
			$el.VlxInfo.Text = "Uncompiled: $($Lsp -join ', ') (sources $pst)"
			$el.VlxInfo.Foreground = & $brush $(if ($pst -eq 'clean') { 'ForestGreen' } else { 'DarkOrange' })
			$ui.vlxSig = 'lsp'
		} elseif ($Vlx.Count -and $sig -ne $ui.vlxSig) {
			$ui.vlxSig = $sig
			$exp = if ($Stamp -and (Test-Path -LiteralPath "$RunDir/$Stamp")) { @(Get-Content -LiteralPath "$RunDir/$Stamp")[0] } else { '' }
			$vs = @($Vlx | ForEach-Object { Test-BenchVlxStamp -Path "$RunDir/$_" -Expected $exp })
			$el.VlxInfo.Text = 'VLX: ' + (($vs | ForEach-Object { $_.text }) -join '   ')
			$worst = if (@($vs | Where-Object { $_.state -in 'bad', 'missing' }).Count) { 'Firebrick' } elseif (@($vs | Where-Object { $_.state -eq 'none' }).Count) { 'DarkOrange' } else { 'ForestGreen' }
			$el.VlxInfo.Foreground = & $brush $worst
		}
		if ($on -and $st -and -not @(Get-ChildItem -LiteralPath $acadDir -Filter *.log -ErrorAction SilentlyContinue).Count) { $el.AcadStatus.Text += "   NO command-line log in $([IO.Path]::GetFullPath($acadDir)): AutoCAD lines are not captured (the bench bundle sets LOGFILEMODE at drawing load; reopen the drawing)" }
		& $files
	}
	# --- Files panel (plan 20 S6): new files since the run started, tagged with the step that was open ---
	$ui.spans = New-Object System.Collections.ArrayList; $ui.fn = 0
	$tracked = @{}; foreach ($t in @(Invoke-Git -AllowNonZeroExit -C $RunDir ls-files)) { $tracked[$t] = $true }   # ponytail: whole-tree walk every 10 s; cache mtimes if it stutters
	$M.tracked = $tracked
	$skipPats = Get-BenchSkip
	$files = {
		param([switch]$Now)
		$ui.fn++; if (-not $Now -and $ui.fn % 5 -and $el.Tabs.SelectedItem -ne $el.TabFiles) { return }   # every 10 s, or each tick on the Files tab
		$rows = New-Object System.Collections.ArrayList
		foreach ($f in @(Get-BenchNewFiles -Root $RunDir -Since $Since.ToUniversalTime() -Skip $tracked | Sort-Object)) {
			$leaf = $f.Substring($f.LastIndexOf('/') + 1); if (@($skipPats | Where-Object { $leaf -like $_ }).Count) { continue }
			$fi = Get-Item -LiteralPath "$RunDir/$f" -Force -ErrorAction SilentlyContinue; if (-not $fi) { continue }
			$sid = Get-BenchFileStep -Spans $ui.spans -Time $fi.LastWriteTime
			if ($sid) { $a = $State.answers[$sid]; if (-not $a -or @($a.files) -notcontains $f) { Add-BenchAnswerFile $M -Rel $f -Id $sid } }
			[void]$rows.Add([pscustomobject]@{ Step = $sid; File = (Get-BenchFullPath -Dir $RunDir -Rel $f); Rel = $f; KB = [Math]::Ceiling($fi.Length / 1KB); Time = $fi.LastWriteTime.ToString('HH:mm:ss') })
		}
		$shown = @{}; foreach ($r in $rows) { $shown[$r.Rel] = $true }
		foreach ($k in @($State.answers.Keys)) {   # attached files (bench-run/files, or ignored ones): listed and sent too
			foreach ($f in @($State.answers[$k].files)) {
				if (-not $f -or $shown[$f]) { continue }; $shown[$f] = $true
				$fi = Get-Item -LiteralPath "$RunDir/$f" -Force -ErrorAction SilentlyContinue; if (-not $fi) { continue }
				[void]$rows.Add([pscustomobject]@{ Step = $k; File = (Get-BenchFullPath -Dir $RunDir -Rel $f); Rel = $f; KB = [Math]::Ceiling($fi.Length / 1KB); Time = $fi.LastWriteTime.ToString('HH:mm:ss') })
			}
		}
		$el.FileList.ItemsSource = $rows
	}
	$el.Tabs.Add_SelectionChanged({
		if ($_.OriginalSource -ne $el.Tabs) { return }
		if ($el.Tabs.SelectedItem -eq $el.TabFiles) { & $files -Now }
		if ($el.Tabs.SelectedItem -ne $el.TabReview -and $el.TabReview.Visibility -eq 'Visible') { $el.TabReview.Visibility = 'Collapsed' }   # a stale review is never pushed
	})
	$el.NoteTabs.Add_SelectionChanged({
			if ($_.OriginalSource -ne $el.NoteTabs) { return }
			if ($el.OutTab.IsSelected) { Show-BenchOutFlag -Tab $el.OutTab -Clear }
		})

	# --- Finish: review page with the files the push sends (plan 20 S6) ---
	$finish = {
		Invoke-BenchCutAcad $M; & $save
		$fh = Invoke-BenchFinishHook -Main $Main -RunDir $RunDir -RunId $RunId -Exe $Exe
		$plan = & $PushPlan
		$el.ReviewList.Items.Clear()
		foreach ($f in @($plan.cand)) {
			$len = (Get-Item -LiteralPath "$RunDir/$f" -Force -ErrorAction SilentlyContinue).Length
			$cb = New-Object "$W.Controls.CheckBox"; $cb.Content = "$(Get-BenchFullPath -Dir $RunDir -Rel $f)   ($([Math]::Ceiling($len / 1KB)) KB)"; $cb.Tag = $f; $cb.IsChecked = $true; $cb.Margin = '4,2'
			[void]$el.ReviewList.Items.Add($cb)
		}
		foreach ($s in $live) {   # AutoCAD error lines per step, folded
			$e = @($State.answers[$s.id].acaderr); if (-not $State.answers[$s.id] -or -not $e.Count) { continue }
			$x = New-Object "$W.Controls.Expander"; $x.Header = "$($s.id): $($e.Count) AutoCAD error line(s)"; $x.Foreground = & $brush 'Firebrick'; $x.Margin = '4,2'
			$tb = New-Object "$W.Controls.TextBlock"; $tb.Text = $e -join "`n"; $tb.FontFamily = 'Consolas'; $tb.Foreground = & $brush 'Black'; $tb.Margin = '18,2'; $x.Content = $tb
			[void]$el.ReviewList.Items.Add($x)
		}
		$left = @($live | Where-Object { -not (& $res $_.id) }).Count
		$el.ReviewHead.Text = "$(@($plan.cand).Count) file(s) to send from the RUN folder $RunDir, plus RESULT.tsv, the filled runbook and bench.patch (all in $RunDir/bench-run).   Answered $($live.Count - $left) / $($live.Count) step(s).$(if ($fh) { "`nbench-finish: $($fh.last)" })"
		$warn = @()
		if ($left) { $warn += "$left step(s) have no answer." }
		if ($fh -and $fh.code -ne 0) {
			$flog = Get-BenchFullPath -Dir $RunDir -Rel 'bench-run/finish.log'
			$warn += "bench-finish failed ($flog): $($fh.last)"
		}
		$miss = @(Get-BenchMissingCollect -Steps $live -Files @($plan.cand) -Dir $RunDir); if ($miss.Count) { $warn += 'Expected logs missing: ' + ($miss -join '; ') }
		foreach ($x in @($plan.strays)) { $warn += "NOT sent (in another run folder): $x" }
		foreach ($x in @($plan.refused)) { $warn += "Refused, over 95 MB: $x" }
		$el.ReviewWarn.Text = $warn -join "`n"
		$el.TabReview.Visibility = 'Visible'; $el.Tabs.SelectedItem = $el.TabReview
	}
	$el.Back.Add_Click({ $el.TabReview.Visibility = 'Collapsed'; $el.Tabs.SelectedItem = $el.TabSteps })
	$el.Push.Add_Click({
		if (Invoke-BenchPushExit -M $M -Picked $Picked -Items $el.ReviewList.Items) { $form.Close() }
	})
	# --- tree ---
	$item = {
		param($kind, $text, $tag, $tip)
		$n = New-Object "$W.Controls.TreeViewItem"; $n.Header = & $head $kind $text; $n.Tag = $tag
		if ($tip) { $n.ToolTip = $tip }; $n
	}
	$refresh = {
		$lids = @($live | ForEach-Object { $_.id })
		$el.Prog.Text = Get-BenchTally -Ids $lids -State $State -Settled ($steps.Count - $live.Count)
		$ui.load = $true; $el.Tree.Items.Clear(); $sel = $null
		$roots = [ordered]@{ open = (& $item $null 'Open' 'r:open' ''); done = (& $item $null $doneRoot 'r:done' ''); settled = (& $item $null 'Settled' 'r:settled' 'Steps whose tasks are already done') }
		if ($ui.reveal) { $ui.exp.Clear() }
		$flt = [string]$el.Filter.SelectedItem.Content
		foreach ($g in @($Rb.groups) + [pscustomobject]@{ id = ''; title = ''; state = '' }) {
			$gs = @($steps | Where-Object { $_.group -eq $g.id }); if (-not $gs.Count) { continue }
			foreach ($part in 'live', 'hidden') {
				$ps = @($gs | Where-Object { [bool]$_.hidden -eq ($part -eq 'hidden') }); if (-not $ps.Count) { continue }
				$rk = if ($part -eq 'hidden') { 'settled' } elseif (@($ps | Where-Object { -not (& $res $_.id) }).Count) { 'open' } else { 'done' }
				$tip = if ($g.state) { "Required state: $($g.state)" } else { '' }
				$gn = & $item $null $(if ($g.id) { "$($g.id): $($g.title)" } else { '(no lane)' }) "g:$($g.id):$rk" $tip
				foreach ($s in $ps) {
					$r = & $res $s.id
					if (($flt -eq 'not answered' -and $r) -or ($flt -eq 'failed' -and $r -ne 'fail')) { continue }
					$n = & $item $(if ($r) { $r } else { 'open' }) $s.id $s.id $s.title
					[void]$gn.Items.Add($n); if ($s.id -eq $ui.cur) { $sel = $n }
					if ($s.id -eq $ui.reveal) { [void]$ui.exp.Add("r:$rk"); [void]$ui.exp.Add($gn.Tag) }
				}
				if ($gn.Items.Count) { [void]$roots[$rk].Items.Add($gn) }
			}
		}
		foreach ($k in $roots.Keys) { if ($k -ne 'settled' -or $roots[$k].Items.Count) { [void]$el.Tree.Items.Add($roots[$k]) } }
		$roots.open.IsExpanded = $true   # R20261104-1504: a collapsed Open root hid every lane after the answered ones
		if ($roots.open.Items.Count) { $roots.open.Items[0].IsExpanded = $true }   # and the first lane with open steps
		$ui.reveal = $null
		foreach ($rn in @($el.Tree.Items)) { foreach ($n in @($rn) + @($rn.Items)) { if ($ui.exp.Contains([string]$n.Tag)) { $n.IsExpanded = $true } } }
		if ($sel) { $sel.Parent.IsExpanded = $true; $sel.Parent.Parent.IsExpanded = $true; $sel.IsSelected = $true; $sel.BringIntoView() }
		$ui.load = $false
	}
	$view = {   # the WPF side of Invoke-BenchShow: note box, required state, page, error bar, output pane
		param($obj, $s)
		$el.Note.IsEnabled = [bool]$s
		$lane = if ($s) { @($Rb.groups) | Where-Object { $_.id -eq $s.group } | Select-Object -First 1 } else { $obj }
		$need = if ($s -and $s.state) { $s.state } elseif ($lane) { [string]$lane.state } else { '' }
		$el.StateLbl.Text = "Required state: $need"; $el.StateBox.Visibility = $(if ($need) { 'Visible' } else { 'Collapsed' })
		& $render $obj
		& $errShow $ui.cur
		if ($ui.job -and $ui.job.step -eq $ui.cur) {   # back on the running step: whole log so far, then keep streaming
			$t = Read-BenchLogTail -Path $ui.job.log -Offset 0; $el.Out.Text = $t.text; $ui.off = $t.offset
			$el.OutHead.Text = "Output: $($ui.cur) run $($ui.job.n) (running)"; $el.Out.ScrollToEnd()
		}
		elseif ($s) { & $showOut $s.id }
		else { $el.Out.Text = ''; $el.OutHead.Text = 'Output' }
	}
	$runJob = {   # Start-BenchStepRun for Invoke-BenchRunBlock: the output pane follows the new job
		param([string]$c, [string]$echo, [string]$sid)
		$j = Start-BenchStepRun -Command $c -Cwd $RunDir -OutDir "$OutDir/out" -Step $sid -Exe $Exe -Echo $echo
		$el.Out.Text = ''; $el.OutHead.Text = "Output: $sid run $($j.n) (running)"
		return $j
	}
	$M.io = @{
		msg = { param($t, $h) [void][Windows.MessageBox]::Show($t, $h) }
		confirm = { param($t, $h) [Windows.MessageBox]::Show($t, $h, 'YesNo', 'Warning') -eq 'Yes' }
		noteGet = { [string]$el.Note.Text }
		noteSet = { param($t) $ui.load = $true; $el.Note.Text = $t; $ui.load = $false }
		out = { param($t) $el.Out.Text = $t }
		head = { param($t) $el.OutHead.Text = $t }
		stop = { param($on) $el.Stop.IsEnabled = [bool]$on; if ($on) { $el.NoteTabs.SelectedItem = $el.OutTab } }
		save = $save; refresh = $refresh; view = $view; pane = $showOut; errShow = $errShow; expect = $expectShow
		cutAcad = { Invoke-BenchCutAcad $M }; runJob = $runJob; now = { Get-Date }
		ask = { param($t, $h) [string][Microsoft.VisualBasic.Interaction]::InputBox($t, $h, '') }
		pick = { $dlg = New-Object Microsoft.Win32.OpenFileDialog; if ($dlg.ShowDialog($form)) { $dlg.FileName } }
	}

	# --- toolbar, keys, events ---
	& $tb 'pass' $null 'Pass (Alt+P)' { Invoke-BenchAnswer $M 'pass' }
	& $tb 'fail' $null 'Fail (Alt+F)' { Invoke-BenchAnswer $M 'fail' }
	& $tb 'blocked' $null 'Blocked (Alt+B)' { Invoke-BenchAnswer $M 'blocked' }
	& $tb 'na' $null 'N/A (Alt+N)' { Invoke-BenchAnswer $M 'na' }
	[void]$el.Tool.Items.Add((New-Object "$W.Controls.Separator"))
	& $tb $null 0xE723 'Attach a file' {
		if (-not $ui.cur) { return }
		$f = & $M.io.pick
		if ($f) { [void](Add-BenchFileCopy $M $f) }
	}
	& $tb $null 0xE722 'Screenshot (whole screen)' { & $snap $false }
	& $tb $null 0xE7A8 'Screenshot of a region (drag a box)' { & $snap $true }
	& $tb $null 0xE77F 'Paste image from the clipboard (Ctrl+V outside the notes)' { & $paste }
	[void]$el.Tool.Items.Add((New-Object "$W.Controls.Separator"))
	& $tb $null 0xE72A 'Next unanswered (Ctrl+Enter)' { Invoke-BenchGo $M 0 }
	& $tb $null 0xE768 'Run this auto step (Alt+A)' { [void](Invoke-BenchKeyRun $M 'A') }
	& $tb $null 0xE8B3 'Run every auto step of this lane, in order (Alt+L)' { [void](Invoke-BenchKeyRun $M 'L') }
	# Start AutoCAD and Rebuild done live on the toolbar, not in the rebuild panel, so they are there in every mode
	# (owner 2026-11-09); the tick enables them: Start while no AutoCAD runs, Rebuild done only in rebuild-first
	[void]$el.Tool.Items.Add((New-Object "$W.Controls.Separator"))
	& $tb $null 0xE7F4 'Start AutoCAD (a bench session of this run)' { Invoke-BenchAcadStart $M } 'TbStart'
	& $tb $null 0xE73E 'Rebuild done (VLX rebuilt in the run folder)' $rbDone 'TbRebuilt'
	$snap = {   # whole virtual screen, or a dragged region of it (plan 20 S7)
		param([bool]$region)
		if (-not $ui.cur) { return }
		$id = $ui.cur; $vs = [System.Windows.Forms.SystemInformation]::VirtualScreen
		$tm = [Windows.PresentationSource]::FromVisual($form).CompositionTarget.TransformToDevice   # ponytail: one DPI for all monitors; mixed scaling under a per-monitor-aware host offsets the region
		$ws = $form.WindowState; $form.WindowState = 'Minimized'; Start-Sleep -Milliseconds 400
		$bmp = New-Object System.Drawing.Bitmap $vs.Width, $vs.Height
		$g = [System.Drawing.Graphics]::FromImage($bmp); $g.CopyFromScreen($vs.Left, $vs.Top, 0, 0, $bmp.Size); $g.Dispose()
		$crop = $null
		if ($region) {
			$ms = New-Object System.IO.MemoryStream; $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png); [void]$ms.Seek(0, 'Begin')
			$bi = New-Object "$W.Media.Imaging.BitmapImage"; $bi.BeginInit(); $bi.CacheOption = 'OnLoad'; $bi.StreamSource = $ms; $bi.EndInit()
			$ov = New-Object "$W.Window"; $ov.WindowStyle = 'None'; $ov.ResizeMode = 'NoResize'; $ov.Topmost = $true; $ov.ShowInTaskbar = $false
			$ov.Left = $vs.Left / $tm.M11; $ov.Top = $vs.Top / $tm.M22; $ov.Width = $vs.Width / $tm.M11; $ov.Height = $vs.Height / $tm.M22; $ov.Cursor = 'Cross'
			$cv = New-Object "$W.Controls.Canvas"; $cv.Background = New-Object "$W.Media.ImageBrush" $bi; $ov.Content = $cv
			$box = New-Object "$W.Shapes.Rectangle"; $box.Stroke = & $brush 'Red'; $box.StrokeThickness = 2; $box.Fill = & $brush '#30FF0000'; [void]$cv.Children.Add($box)
			$drag = @{ on = $false; x = 0; y = 0; r = $null }
			$ov.Add_KeyDown({ if ($_.Key -eq 'Escape') { $ov.Close() } })
			$cv.Add_MouseLeftButtonDown({
				$p = $_.GetPosition($cv); $drag.on = $true; $drag.x = $p.X; $drag.y = $p.Y
				[Windows.Controls.Canvas]::SetLeft($box, $p.X); [Windows.Controls.Canvas]::SetTop($box, $p.Y); $box.Width = 0; $box.Height = 0
				[void]$cv.CaptureMouse()
			})
			$cv.Add_MouseMove({
				if (-not $drag.on) { return }
				$p = $_.GetPosition($cv)
				[Windows.Controls.Canvas]::SetLeft($box, [Math]::Min($p.X, $drag.x)); [Windows.Controls.Canvas]::SetTop($box, [Math]::Min($p.Y, $drag.y))
				$box.Width = [Math]::Abs($p.X - $drag.x); $box.Height = [Math]::Abs($p.Y - $drag.y)
			})
			$cv.Add_MouseLeftButtonUp({
				if (-not $drag.on) { return }
				$drag.on = $false; $cv.ReleaseMouseCapture()
				$x = [int]([Windows.Controls.Canvas]::GetLeft($box) * $tm.M11); $y = [int]([Windows.Controls.Canvas]::GetTop($box) * $tm.M22)
				$w = [int]($box.Width * $tm.M11); $h = [int]($box.Height * $tm.M22)
				if ($w -gt 4 -and $h -gt 4) { $drag.r = New-Object System.Drawing.Rectangle $x, $y, $w, $h }
				$ov.Close()
			})
			[void]$ov.ShowDialog(); $ms.Dispose()
			if ($drag.r) { $drag.r = [System.Drawing.Rectangle]::Intersect($drag.r, (New-Object System.Drawing.Rectangle 0, 0, $bmp.Width, $bmp.Height)) }   # rounding at 125/150 %
			if ($drag.r -and $drag.r.Width -gt 4 -and $drag.r.Height -gt 4) { $crop = $bmp.Clone($drag.r, $bmp.PixelFormat) }
		}
		$out = if ($region) { $crop } else { $bmp }
		if ($out) {
			$name = "$id-$(Get-Date -Format 'yyyyMMdd-HHmmss').png"; $out.Save("$(& $fileDir)/$name", [System.Drawing.Imaging.ImageFormat]::Png)
			Add-BenchAnswerFile $M -Rel "bench-run/files/$name" -Id $id
		}
		if ($crop) { $crop.Dispose() }; $bmp.Dispose(); $form.WindowState = $ws; [void]$form.Activate()
	}
	$paste = {   # clipboard image -> PNG; copied files -> attachments
		if (-not $ui.cur) { return }
		try { $img = if ([Windows.Clipboard]::ContainsImage()) { [Windows.Clipboard]::GetImage() } else { $null }; $drop = [Windows.Clipboard]::ContainsFileDropList() }
		catch { [Windows.MessageBox]::Show("The clipboard is busy: $_", 'Paste') | Out-Null; return }
		if ($img) {
			$name = "$($ui.cur)-paste-$(Get-Date -Format 'yyyyMMdd-HHmmss').png"
			$enc = New-Object "$W.Media.Imaging.PngBitmapEncoder"; $enc.Frames.Add([Windows.Media.Imaging.BitmapFrame]::Create($img))
			$fs = [IO.File]::Create("$(& $fileDir)/$name"); try { $enc.Save($fs) } finally { $fs.Dispose() }
			Add-BenchAnswerFile $M -Rel "bench-run/files/$name"
		} elseif ($drop) {
			foreach ($f in [Windows.Clipboard]::GetFileDropList()) {
				if (Test-Path -LiteralPath $f -PathType Leaf) { [void](Add-BenchFileCopy $M $f) }
			}
		} else { [Windows.MessageBox]::Show('The clipboard has no image or file.', 'Paste') | Out-Null }
	}

	$onTree = {
		if (-not $ui.load -and $el.Tree.SelectedItem) { Invoke-BenchShow $M ([string]$el.Tree.SelectedItem.Tag) }
	}
	$el.Tree.Add_SelectedItemChanged($onTree)
	$el.Tree.AddHandler([Windows.Controls.TreeViewItem]::ExpandedEvent, [Windows.RoutedEventHandler]{ if (-not $ui.load) { [void]$ui.exp.Add([string]$args[1].OriginalSource.Tag) } })
	$el.Tree.AddHandler([Windows.Controls.TreeViewItem]::CollapsedEvent, [Windows.RoutedEventHandler]{ if (-not $ui.load) { [void]$ui.exp.Remove([string]$args[1].OriginalSource.Tag) } })
	$onNote = { if (-not $ui.load -and $ui.cur) { (Get-BenchAnswer $M $ui.cur).note = $el.Note.Text; & $save } }
	$el.Note.Add_TextChanged($onNote)
	$el.Gen.Add_TextChanged({ & $save })
	$el.Filter.Add_SelectionChanged({ if ($el.Prog) { & $refresh } })
	$el.OnTop.Add_Click({ $form.Topmost = [bool]$el.OnTop.IsChecked })
	# Uncompiled / compiled toggle (ust 2026-11-09): default uncompiled when [bench] lsp is set
	$el.Uncompiled = $form.FindName('Uncompiled')
	if ($Lsp.Count -and $RunDir) {
		$el.Uncompiled.Visibility = 'Visible'; $el.Uncompiled.IsChecked = ((Get-BenchLoadMode -RunDir $RunDir) -eq 'lsp')
		$el.Uncompiled.Add_Click({ Invoke-BenchLoadModeClick $M ([bool]$el.Uncompiled.IsChecked) })
	}
	$onKey = {   # Get-BenchKeyAction decides; Alt+A / Alt+L are handled only when Invoke-BenchKeyRun takes them
		$e = $_
		$k = if ($e.Key -eq 'System') { [string]$e.SystemKey } else { [string]$e.Key }
		$kp = @{ Key = $k; Mods = [string]$e.KeyboardDevice.Modifiers; Steps = $el.Tabs.SelectedItem -eq $el.TabSteps }
		$ka = Get-BenchKeyAction @kp -TextFocus ($el.Note.IsKeyboardFocusWithin -or $el.Gen.IsKeyboardFocusWithin)
		if (-not $ka) { return }
		switch ($ka.act) {
			'go' { $e.Handled = $true; Invoke-BenchGo $M $ka.arg }
			'paste' { $e.Handled = $true; & $paste }
			'answer' { $e.Handled = $true; Invoke-BenchAnswer $M $ka.arg }
			'run' { if (Invoke-BenchKeyRun $M $ka.arg) { $e.Handled = $true } }
		}
	}
	$form.Add_PreviewKeyDown($onKey)
	$el.Abort.Add_Click({
		if (Invoke-BenchAbort $M (& $M.io.ask 'Reason for aborting this run:' 'Abort run')) { $form.Close() }
	})
	$el.Finish.Add_Click({ & $finish })
	$onClosing = {   # Abort and Push checked already (ui.closing); else the close checks (Test-BenchCanClose)
		$e = $args[1]
		if ($ui.closing) { return }
		if (-not (Test-BenchCanClose $M)) { $ui.exit = ''; $Picked.Clear(); $e.Cancel = $true }
	}
	$form.Add_Closing($onClosing)
	foreach ($pk in @(Invoke-BenchWindowOpen $M)) { Write-Verbose "auto run of $pk closed as FAIL" }
	$onShown = {   # the first live step opens, then the timer starts
		$first = @($live)[0]; if (-not $first) { $first = @($steps)[0] }
		if ($first) { Invoke-BenchSelect $M $first.id }
		$timer.Start()
	}
	$form.Add_ContentRendered($onShown)
	# an error in any handler shows a message instead of closing the window ($ErrorActionPreference is Stop)
	$form.Dispatcher.Add_UnhandledException({ $_.Handled = $true; [Windows.MessageBox]::Show("git-sp window error: $($_.Exception.Message)", 'git-sp') | Out-Null })
	[void]$form.ShowDialog()
	$timer.Stop(); & $save
	return $ui.exit
}

function Invoke-BenchTest {
	param([string]$Main, [string]$StartDir)
	$ini = Get-BenchIni
	if (-not $ini) { throw 'No .bench.ini on origin/main. Run -Bench pull first.' }
	$runId = Resolve-BenchRunId -Main $Main -StartDir $StartDir
	if (-not $runId) { $runId = @(Select-BenchRun -Runs (Get-BenchRuns $ini 'open'))[0] }
	if (-not $runId -or -not $ini.Contains($runId)) { throw 'No run chosen. Use -Run <id>.' }
	if ($ini[$runId].state -ne 'open') { throw "Run $runId is not open (state '$($ini[$runId].state)')." }
	$sec = $ini[$runId]
	$wt = Get-BenchWorktree $Main $runId
	$tag = if ($sec.tag) { $sec.tag } else { "bench/$runId" }
	if (-not $sec.runbook) { throw "Run $runId has no runbook= in .bench.ini on origin/main." }
	$rbPath = "$wt/$($sec.runbook)"
	if (-not (Test-Path -LiteralPath "$wt/.git")) { throw "Run folder $wt does not exist; -Bench test could not create it (see the pull lines above)." }
	if (-not (Test-Path -LiteralPath $rbPath)) {
		[void](Invoke-Git -AllowNonZeroExit cat-file -e "refs/tags/${tag}:$($sec.runbook)")
		if ($LASTEXITCODE -eq 0) { throw "Runbook $($sec.runbook) is in $tag but not on disk at ${rbPath} (RUN folder ${wt}): the run folder is out of date or its sparse cone leaves that folder out. Run -Bench test again (it refreshes the folder) or add the folder to the cone (git-sp picker)." }
		throw "Runbook $($sec.runbook) (expected at ${rbPath}) is not in ${tag}: the tag was made before the runbook was committed, or runbook= is wrong. Re-tag the run or fix .bench.ini."
	}
	$rb = Read-Runbook -Path $rbPath -Tokens (Get-BenchTokens -Run $wt -Main $Main)
	$out = "$wt/bench-run"
	New-Item -ItemType Directory -Path $out -Force | Out-Null
	$state = Import-RunState -Path "$out/results.json"
	$task = @(([string]$sec.tasks) -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })[0]
	# settled steps: hidden when every task is done in origin/main's ledger (30-TODO + 35-DONE)
	$ledger = (@(foreach ($d in 'docs/30-TODO.md', 'docs/35-DONE.md') { Invoke-Git -AllowNonZeroExit show "origin/main:$d" }) -join "`n")
	foreach ($s in $rb.steps) { if ($s.settled) { $s.hidden = Test-BenchTaskSettled -Ledger $ledger -Task $(if ($s.task) { $s.task } else { $task }) } }
	[void](Hide-BenchModeStep -Rb $rb -Mode (Get-BenchLoadMode -RunDir $wt))
	Set-BenchAcadHook -Main $Main -RunId $runId -Ini $ini
	$wtitle = "Bench $runId - git-sp $(Get-BenchBuildId)"
	$picked = New-Object System.Collections.ArrayList
	$plan = { Get-BenchPushPlan -Main $Main -Wt $wt -Sec $sec -RunId $runId }   # called from the window, which is below this frame: no closure needed
	# one window per run: a second one would save its older answers over the first one's (results.json)
	$lock = "$out/window.pid"
	$other = if (Test-Path -LiteralPath $lock) { Get-Process -Id ([int]([IO.File]::ReadAllText($lock).Trim())) -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $PID -and $_.ProcessName -match '^(powershell|pwsh)$' } }   # ponytail: a reused PID of another PowerShell blocks; delete window.pid then
	if ($other) { throw "The runbook window of $runId is already open (PID $($other.Id)). Use that window, or close it first." }
	[IO.File]::WriteAllText($lock, [string]$PID)
	$bcfg = if ($ini -and $ini.Contains('bench')) { $ini['bench'] } else { @{} }   # repo-level [bench]: acad, vlx, stamp
	$rwArgs = @{
		Title = $wtitle; Rb = $rb; State = $state; OutDir = $out; RunDir = $wt; PushPlan = $plan; Picked = $picked
		Acad = $(if ([string]$bcfg.acad) { [string]$bcfg.acad } else { Find-BenchAcad -Rb $rb }); Main = $Main; RunId = $runId
		Stamp = ([string]$bcfg.stamp)
		Vlx = Get-BenchVlxList -Bcfg $bcfg; Lsp = Get-BenchLspList -Bcfg $bcfg
		ClearEnv = @(([string]$bcfg.clearenv -split ';') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
	}
	try {
	$how = Show-RunbookWindow @rwArgs -Since (Get-BenchSince -Wt $wt -Tag $tag).ToLocalTime()
	} finally { Remove-Item -LiteralPath $lock -Force -ErrorAction Ignore }
	if ($how -eq 'finish' -or $how -eq 'abort') {
		Complete-BenchRunbook -Runbook $rbPath -OutDir $out -Steps $rb.steps -State $state -DefaultTask $task
		$script:Run = $runId   # the window's review page picked the files
		if ($picked.Count) { $script:Files = @($picked); $script:NonInteractive = $true }
		Invoke-BenchPush -Main $Main -StartDir $StartDir
	}
}

# --- AutoCAD bench hook (T66, reworked: bench session only) -------------------
# git-sp writes %APPDATA%/Autodesk/ApplicationPlugins/git-sp-bench.bundle. Its
# LISP runs in every drawing of every AutoCAD and tells two sessions apart by the
# per-process variable GSB_BENCH_RUN, which only the window's Start AutoCAD sets
# (for that child; it vanishes with the process):
#  - BENCH session (GSB_BENCH_RUN = an open run): the run's folders (root + the
#    [bench] support = dirs, default build;menu) go FIRST in the support path and
#    the main clone's entries go out; the owner's support path is saved ONCE to
#    Contents/acad-support.txt; the run's load file is loaded (gsb:bench T,
#    gsb:run, gsb:repo set first); TRUSTEDPATHS gets the run; log into the run.
#  - NORMAL session (anything else): no run file is loaded; the saved support
#    path is put back (file deleted) else stale <repo>-bench-R* entries are
#    dropped; [bench] clearenv = names whose value is a bench run folder are
#    unset ((setenv NAME "")); the log settings are put back. An aborted bench
#    session is healed at the next normal start.
# Contents/runs/<main leaf>.txt holds one line '<run>|<load file>|<main root>'
# (the old 2-field form still reads) or nothing (Finish / no run).
# Every load writes <run>\bench-run\acad-status.txt (bench=yes|no, run=, support-first=).
# Every step is traced, one line each, to <bundle Contents>\logs\bench-trace-bundle.log and, once a run is
# picked, also to <run>\logs\bench-trace-bundle.log; the load file's trace is <run>\logs\bench-trace-acaddoc.log.
# Finish collects both (any *.log in the run folder).
function Get-BenchAcadLisp {
	param([string]$RunsDir, [string]$Support = 'build;menu', [string[]]$ClearEnv = @())
	$l = @'
;; git-sp-bench.lsp - written by git-sp -Bench; rewritten on every pull/test, do not edit.
(vl-load-com)
;; trace (like ustb:trace): one line per event, file opened-written-closed per line, never throws.
;; The run folder is unknown until the pick: lines go to <bundle Contents>\logs\bench-trace-bundle.log (*gsb:log*)
;; always, and, once a run is picked, also to <run>\logs\bench-trace-bundle.log (*gsb:rlog*).
(setq *gsb:log* "__SELF__\\logs\\bench-trace-bundle.log" *gsb:rlog* nil)
(defun gsb:str (v) (vl-princ-to-string v))
(defun gsb:trace (txt)
  (vl-catch-all-apply
    '(lambda (/ h f line)
       (setq line (strcat (if (numberp (getvar "CDATE")) (rtos (getvar "CDATE") 2 6) "no-time")
                          " [" (gsb:str (getvar "DWGNAME")) "] " (gsb:str txt)))
       (foreach f (list *gsb:log* *gsb:rlog*)
         (if (and (= (type f) 'STR) (setq h (open f "a")))
           (progn (vl-catch-all-apply 'write-line (list line h)) (close h)))))
    nil)
  txt)
;; stage: BEGIN, run, END -> value or ERROR name: message; returns (T . value) or (nil . message)
(defun gsb:stage (name fn args / r m)
  (gsb:trace (strcat "BEGIN " name))
  (setq r (vl-catch-all-apply fn args))
  (if (vl-catch-all-error-p r)
    (progn
      (setq m (vl-catch-all-error-message r))
      (gsb:trace (strcat "ERROR " name ": " m))
      (princ (strcat "\ngit-sp bench: ERROR in " name ": " m "\ngit-sp bench: trace " (gsb:str *gsb:log*)))
      (cons nil m))
    (progn (gsb:trace (strcat "END " name " -> " (gsb:str r))) (cons T r))))
;; value of a stage, nil when it failed
(defun gsb:stg (name fn args / x) (if (car (setq x (gsb:stage name fn args))) (cdr x)))
(defun gsb:mkdir (d) (vl-catch-all-apply 'vl-mkdir (list d)))
(gsb:mkdir "__SELF__\\logs")
(defun gsb:split (s / i r)
  (setq r '())
  (while (setq i (vl-string-search ";" s))
    (setq r (cons (substr s 1 i) r) s (substr s (+ i 2))))
  (reverse (cons s r)))
(defun gsb:join (l / r)
  (setq r "")
  (foreach x l (setq r (if (= r "") x (strcat r ";" x))))
  r)
(defun gsb:norm (p / q)
  (setq q (strcase (vl-string-translate "/" "\\" p)))
  (if (and (> (strlen q) 4) (= (substr q (- (strlen q) 3)) "\\...")) (setq q (substr q 1 (- (strlen q) 4))))
  (vl-string-right-trim "\\" q))
(defun gsb:keep-p (p keep)
  (vl-some '(lambda (k) (= 0 (vl-string-search (strcat (gsb:norm k) "\\") (strcat (gsb:norm p) "\\")))) keep))
(defun gsb:fix (lst keep add / out)
  (setq out '())
  (foreach p lst
    (if (and (/= p "") (or (gsb:keep-p p keep) (not (wcmatch (gsb:norm p) "*-BENCH-R########-####*"))))
      (setq out (cons p out))))
  (setq out (reverse out))
  (foreach a add (if (not (member (strcase a) (mapcar 'strcase out))) (setq out (append out (list a)))))
  out)
(defun gsb:bsplit (s / i r)
  (setq r '())
  (while (setq i (vl-string-search "|" s))
    (setq r (cons (substr s 1 i) r) s (substr s (+ i 2))))
  (reverse (cons s r)))
;; runs line: '<run>|<load file>|<main clone root>'; the old 2-field form (no main root) still reads
(defun gsb:runs (/ d h l r p)
  (setq d "__RUNS__" r '())
  (foreach f (vl-directory-files d "*.txt" 1)
    (if (setq h (open (strcat d "/" f) "r"))
      (progn
        (while (setq l (read-line h))
          (if (> (length (setq p (gsb:bsplit l))) 1)
            (setq r (cons (list (car p) (cadr p) (vl-filename-base f) (if (caddr p) (caddr p) "")) r))))
        (close h))))
  (reverse r))
;; a flag/env value is set only when (and s (/= s "")): setenv cannot delete, "" is unset
(defun gsb:env (n / s) (setq s (getenv n)) (if (and s (/= s "")) s))
;; <run>\\bench-run\\load-mode.txt -> ("lsp" (full path ...)) | ("vlx" nil); no file = vlx (ust 2026-11-09)
(defun gsb:mode-read (dir / f h m l out i)
  (setq f (strcat dir "\\bench-run\\load-mode.txt"))
  (if (and (findfile f) (setq h (open f "r")))
    (progn (setq m (read-line h) l (read-line h)) (close h)))
  (if (and m l (= (vl-string-trim " \t" m) "lsp"))
    (progn
      (while (setq i (vl-string-search "," l))
        (setq out (cons (substr l 1 i) out) l (substr l (+ i 2))))
      (setq out (vl-remove-if '(lambda (x) (= x ""))
                  (mapcar '(lambda (x) (vl-string-trim " \t" x)) (reverse (cons l out)))))
      (if out
        (list "lsp" (mapcar '(lambda (x) (strcat (vl-string-right-trim "\\" dir) "\\"
                                                 (vl-string-translate "/" "\\" x)))
                            out))
        (list "vlx" nil)))
    (list "vlx" nil)))
(defun gsb:pick (runs e)
  (car (vl-remove-if-not '(lambda (r) (= (gsb:norm (car r)) (gsb:norm e))) runs)))
(defun gsb:support-now () (vla-get-SupportPath (vla-get-Files (vla-get-Preferences (vlax-get-acad-object)))))
;; the owner's own value of a setting, saved ONCE before the first bench session changes it; -> "saved" | "kept"
(defun gsb:save-once (f old / h)
  (cond ((findfile f) "kept")
        ((setq h (open f "w")) (write-line old h) (close h) "saved")
        (T "not saved")))
(defun gsb:read-once (f / h s)
  (if (and (findfile f) (setq h (open f "r")))
    (progn (setq s (read-line h)) (close h) s)))
(defun gsb:save-support (old) (gsb:save-once "__SELF__\\acad-support.txt" old))
(defun gsb:read-support (/ f h s)
  (setq f "__SELF__\\acad-support.txt")
  (if (and (findfile f) (setq h (open f "r")))
    (progn (setq s (read-line h)) (close h) s)))
;; plan 20: the window reads <run>\bench-run\acad-status.txt (what this drawing loaded)
;; the run's load file writes <run>\\bench-run\\load-result.txt (loaded <build> | refused <reason>); read after the load
(defun gsb:result (r / f h s)
  (setq f (strcat (car r) "\\bench-run\\load-result.txt"))
  (if (and (findfile f) (setq h (open f "r")))
    (progn (setq s (read-line h)) (close h)))
  (gsb:trace (strcat "load-result " f ": " (gsb:str s)))
  (if (= (type s) 'STR) s ""))
(defun gsb:status (r ok bench / h d)
  (setq d (strcat (car r) "\\bench-run"))
  (vl-mkdir d)
  (if (setq h (open (strcat d "\\acad-status.txt") "w"))
    (progn
      (write-line (strcat "time=" (menucmd "M=$(edtime,$(getvar,date),YYYY-MO-DD HH:MM:SS)")) h)
      (write-line (strcat "bench=" (if bench "yes" "no")) h)
      (write-line (strcat "run=" (if bench (car r) "")) h)
      (write-line (strcat "support-first=" (car (gsb:split (gsb:support-now)))) h)
      (write-line (strcat "acadver=" (getvar "ACADVER")) h)
      (write-line (strcat "secureload=" (itoa (getvar "SECURELOAD"))) h)
      (write-line (strcat "trusted=" (if (gsb:keep-p "__SELF__" (gsb:split (getvar "TRUSTEDPATHS"))) "yes" "no")) h)
      (write-line (strcat "logfile=" (vl-princ-to-string (getvar "LOGFILENAME"))) h)
      (write-line (strcat "load=" ok) h)
      (write-line (strcat "result=" (if bench (gsb:result r) "")) h)
      (write-line (strcat "dwg=" (getvar "DWGPREFIX") (getvar "DWGNAME")) h)
      (foreach l (gsb:status-tail) (write-line l h))
      (close h)))
  (if bench (gsb:docline d ok)))
;; the session lines of acad-status.txt (nil-safe, tested headless): nonce, window, open drawings and their paths
(defun gsb:status-tail ()
  (list (strcat "nonce=" (gsb:str (gsb:env "GSB_BENCH_NONCE")))
        (strcat "hwnd=" (gsb:str (gsb:try 'gsb:hwnd nil)))
        (strcat "docs=" (gsb:str (gsb:try 'gsb:doc-count nil)))
        (strcat "docpaths=" (gsb:str (gsb:try 'gsb:doc-paths nil)))))
(defun gsb:hwnd () (vla-get-HWND (vlax-get-acad-object)))
;; plan 30 S3: one line per drawing of this session in <run>\bench-run\acad-docs.txt (the newest line for a name wins)
;; the acad-docs.txt line (pure, tested headless)
(defun gsb:docline-text (n time ok prefix name)
  (strcat "nonce=" n " time=" time " load=" (vl-string-translate " " "_" ok)
          " doc=" (vl-string-translate "\\" "/" (strcat prefix name))))
;; the lines of session n (pure): older sessions are pruned at the session's first write
(defun gsb:docline-keep (lines n / me)
  (setq me (strcat "nonce=" n " "))
  (vl-remove-if-not '(lambda (l) (= 0 (vl-string-search me l))) lines))
;; One line per drawing load, appended (ust review M5): 'nonce=<n> time=<t> load=<token> doc=<full path>'; the
;; load token has no spaces. The first line of a new session drops the lines of older sessions.
(defun gsb:docline (d ok / f h l all n)
  (setq f (strcat d "\\acad-docs.txt") n (gsb:str (gsb:env "GSB_BENCH_NONCE")) all '())
  (if (setq h (open f "r"))
    (progn
      (while (setq l (read-line h)) (setq all (cons l all)))
      (close h)))
  (if (setq h (open f "w"))
    (progn
      (foreach l (gsb:docline-lines (reverse all) n (menucmd "M=$(edtime,$(getvar,date),YYYY-MO-DD HH:MM:SS)") ok
                                    (getvar "DWGPREFIX") (getvar "DWGNAME"))
        (write-line l h))
      (close h))))
;; the new acad-docs.txt (pure, tested headless): this session's lines, then the new one
(defun gsb:docline-lines (all n time ok prefix name)
  (append (gsb:docline-keep all n) (list (gsb:docline-text n time ok prefix name))))
;; open drawings of this AutoCAD
(defun gsb:doc-count () (vla-get-count (vla-get-documents (vlax-get-acad-object))))
;; their full paths, / slashes, joined with | (ust review N9: the judge compares them with the drawings seen)
(defun gsb:doc-paths (/ r)
  (vlax-for d (vla-get-documents (vlax-get-acad-object))
    (setq r (cons (vl-string-translate "\\" "/" (vla-get-FullName d)) r)))
  (gsb:join-with (reverse r) "|"))
(defun gsb:join-with (l sep / r)
  (setq r "")
  (foreach x l (setq r (if (= r "") x (strcat r sep x))))
  r)
;; TRUSTEDPATHS for this session (pure, tested headless; ust review M7, N10): the saved owner list (or old), plus
;; entries the owner added since the save (exact match, not a bench folder, not the bundle), the run kept, the bundle
;; and keep\... added; the main clone's entries dropped in a bench session.
(defun gsb:trusted-merge (old saved keep self main / base own new sv)
  (setq base (if saved saved old) sv (mapcar 'gsb:norm (gsb:split (if saved saved ""))))
  (if saved
    (foreach p (gsb:split old)
      (if (and (/= p "") (not (member (gsb:norm p) sv)) (/= (gsb:norm p) (gsb:norm self))
               (not (wcmatch (gsb:norm p) "*-BENCH-R########-####*")))
        (setq own (cons p own)))))
  (setq new (gsb:fix (append (gsb:split base) (reverse own)) keep
                     (cons self (mapcar '(lambda (k) (strcat k "\\...")) keep))))
  (if (/= main "") (setq new (vl-remove-if '(lambda (p) (gsb:keep-p p (list main))) new)))
  (gsb:join new))
;; this session's TRUSTEDPATHS from the current one (tested headless): the owner's saved list, the run (r) kept,
;; the bundle added, the run's main clone dropped
(defun gsb:trusted-new (old r)
  (gsb:trusted-merge old (gsb:read-once "__SELF__\\acad-trusted.txt") (if r (list (car r))) "__SELF__"
                     (if r (nth 3 r) "")))
(defun gsb:trusted-now () (getvar "TRUSTEDPATHS"))
;; a value, or nil when the call fails
(defun gsb:try (fn args / r) (if (not (vl-catch-all-error-p (setq r (vl-catch-all-apply fn args)))) r))
;; plan 20: command-line log into <first run>\logs\acad while a run is loaded;
;; the user's LOGFILEMODE / LOGFILEPATH are saved once and put back when no run is loaded
(defun gsb:log (runs / f h p m)
  (setq f "__SELF__\\acad-log.txt")
  (if runs
    (progn
      (if (not (findfile f))
        (if (setq h (open f "w"))
          (progn (write-line (itoa (getvar "LOGFILEMODE")) h) (write-line (getvar "LOGFILEPATH") h) (close h))))
      (setq p (strcat (car (car runs)) "\\logs"))
      (vl-mkdir p)
      (setq p (strcat p "\\acad"))
      (vl-mkdir p)
      (if (/= (strcase (vl-string-right-trim "\\" (getvar "LOGFILEPATH"))) (strcase p))
        (progn (setvar "LOGFILEMODE" 0) (setvar "LOGFILEPATH" (strcat p "\\"))))
      (setvar "LOGFILEMODE" 1))
    (if (and (findfile f) (setq h (open f "r")))
      (progn
        (setq m (read-line h) p (read-line h))
        (close h)
        (if p (setvar "LOGFILEPATH" p))
        (if m (setvar "LOGFILEMODE" (atoi m)))
        (vl-file-delete f)))))
;; load returns the value of the file's last form; a file that ends in a failed
;; (vl-catch-all-apply ...) returns an error object, which is not a load fault: answer T
(defun gsb:load (f) (load f) T)
(defun gsb:put-support (s)
  (vla-put-SupportPath (vla-get-Files (vla-get-Preferences (vlax-get-acad-object))) s))
(defun gsb:main (/ runs e r old new st base dirs v x saved)
  (gsb:trace (strcat "START ACADVER=" (gsb:str (getvar "ACADVER")) " LISPSYS=" (gsb:str (getvar "LISPSYS"))
                     " SECURELOAD=" (gsb:str (getvar "SECURELOAD")) " DWGNAME=" (gsb:str (getvar "DWGNAME"))))
  (gsb:trace (strcat "TRUSTEDPATHS=" (gsb:str (getvar "TRUSTEDPATHS"))))
  (gsb:trace (strcat "SUPPORT=" (gsb:str (gsb:stg "support path" 'gsb:support-now nil))))
  (setq e (gsb:stg "env GSB_BENCH_RUN" 'gsb:env '("GSB_BENCH_RUN")))
  (gsb:stg "env GSB_BENCH_REPO" 'gsb:env '("GSB_BENCH_REPO"))
  (setq runs (gsb:stg "runs read" 'gsb:runs nil))
  ;; BENCH session = started by the window's Start AutoCAD (GSB_BENCH_RUN is a per-process variable, gone with that process);
  ;; every other AutoCAD is a NORMAL session and loads the main clone
  (setq r (if e (gsb:stg "pick run" 'gsb:pick (list runs e))))
  (if (and e (not r)) (princ (strcat "\ngit-sp bench: GSB_BENCH_RUN " e " is not an open run; normal session.")))
  (if r
    (progn   ; from here every line also goes to the run's own log; the lines before it are in the bundle log only
      (gsb:mkdir (strcat (car r) "\\logs"))
      (setq *gsb:rlog* (strcat (car r) "\\logs\\bench-trace-bundle.log"))
      (gsb:trace (strcat "RUN " (gsb:str (car r)) " (earlier lines: " *gsb:log* ")")))
    (gsb:trace "NORMAL session (no run picked)"))
  (setq gsb:bench nil gsb:run nil gsb:repo nil gsb:mode nil gsb:lsp nil)
  (setq old (gsb:support-now))
  (if r
    (progn   ; run folders first, the main clone's entries out, for this session only (the original is saved to restore)
      (gsb:stg "save support" 'gsb:save-support (list old))
      (setq base (if (gsb:read-support) (gsb:read-support) old)
            dirs (cons (car r) (mapcar '(lambda (d) (strcat (vl-string-right-trim "\\" (car r)) "\\" d)) '__SUPPORT__))
            new (vl-remove-if '(lambda (p) (or (and (/= (nth 3 r) "") (gsb:keep-p p (list (nth 3 r))))
                                               (member (gsb:norm p) (mapcar 'gsb:norm dirs))))
                              (gsb:fix (gsb:split base) nil nil))
            new (gsb:join (append dirs new))))
    (setq new (if (setq base (gsb:read-support)) base (gsb:join (gsb:fix (gsb:split old) nil nil)))))
  (gsb:trace (strcat "SUPPORT before=" (gsb:str old)))
  (if (/= new old) (gsb:stg "put SupportPath" 'gsb:put-support (list new)))
  (gsb:trace (strcat "SUPPORT after=" (gsb:str (gsb:stg "support path" 'gsb:support-now nil))))
  (if (and (not r) (findfile "__SELF__\\acad-support.txt")) (vl-file-delete "__SELF__\\acad-support.txt"))
  (setq old (gsb:trusted-now))
  ;; plan 30 S2: a bench session trusts the run, not the main clone; the owner's list is saved once and put back
  (if r (gsb:stg "save trusted" 'gsb:save-once (list "__SELF__\\acad-trusted.txt" old)))
  (setq saved (gsb:read-once "__SELF__\\acad-trusted.txt"))
  (setq new (gsb:trusted-new old r))
  (gsb:trace (strcat "TRUSTED before=" (gsb:str old)))
  (if (/= new old) (gsb:stg "set TRUSTEDPATHS" 'setvar (list "TRUSTEDPATHS" new)))
  ;; the saved list goes only once it is back (a failed setvar keeps it for the next normal session)
  (if (and (not r) saved (= (strcase (gsb:trusted-now)) (strcase new)))
    (vl-file-delete "__SELF__\\acad-trusted.txt"))
  (gsb:trace (strcat "TRUSTED after=" (gsb:str (gsb:trusted-now))))
  ;; the bundle's own folder: after one load (SECURELOAD 0 or "Always load") it stays trusted, so SECURELOAD can go back on
  (if (and (not (gsb:keep-p "__SELF__" (gsb:split old))) (gsb:keep-p "__SELF__" (gsb:split (gsb:trusted-now))))
    (princ "\ngit-sp bench: bundle folder __SELF__ added to Trusted Locations; SECURELOAD can be set back to 1."))
  (if r
    (progn
      (setq st "none" gsb:bench T gsb:run (car r) gsb:repo (caddr r))   ; before the load: the load file's own run folder and repo (main clone leaf)
      ;; gsb:mode "lsp" (load gsb:lsp, the uncompiled loaders) or "vlx"; the load file picks (ust 2026-11-09)
      (setq x (gsb:mode-read (car r)) gsb:mode (car x) gsb:lsp (cadr x))
      (gsb:trace (strcat "MODE " gsb:mode (if gsb:lsp (strcat " " (gsb:str gsb:lsp)) "")))
      (cond
        ;; rebuild-first (stale committed VLX): nothing of the run is loaded, a loaded VLX cannot be unloaded
        ((and (/= gsb:mode "lsp") (findfile (strcat (car r) "\\bench-run\\autoload.off")))
         (setq st "off")
         (gsb:trace (strcat "NOLOAD " (car r) "\\bench-run\\autoload.off exists"
                            " (rebuild first, in the RUN folder " (car r) ")")))
        ((and (/= (cadr r) "") (findfile (cadr r)))
         (if (car (setq x (gsb:stage (strcat "load " (cadr r)) 'gsb:load (list (cadr r)))))
           (progn (setq st "ok") (princ (strcat "\ngit-sp bench: loaded " (cadr r) " in " (getvar "DWGNAME"))))
           (progn (setq st (strcat "fail " (cdr x)))
                  (princ (strcat "\ngit-sp bench: FAIL loading " (cadr r) " in " (getvar "DWGNAME") ": " (cdr x))))))
        (T (gsb:trace (strcat "NOLOAD load file " (gsb:str (cadr r)) " is empty or not found"))))
      (gsb:stage "status" 'gsb:status (list r st T)))
    (progn   ; normal session: no run file; env values a bench run left behind (setenv persists) are unset
      (foreach n '__CLEARENV__
        (setq v (getenv n))
        (if (and v (/= v "") (wcmatch (gsb:norm v) "*-BENCH-R########-####*")) (setenv n "")))
      (foreach x runs (gsb:stage (strcat "status " (nth 2 x)) 'gsb:status (list x "none" nil)))))
  (gsb:stage "log setup" 'gsb:log (list (if r (list r))))
  (gsb:trace "DONE")
  (princ))
(if (not (car (setq gsb:err (gsb:stage "main" 'gsb:main nil))))
  (princ (strcat "\ngit-sp bench: FAIL " (cdr gsb:err))))
(princ)
'@
	$self = ((Split-Path -Parent $RunsDir) -replace '/', '\').Replace('\', '\\')   # Contents folder, backslashes escaped for a LISP string
	$dirs = @(([string]$Support -split ';') | ForEach-Object { $_.Trim() -replace '/', '\' })
	$dirs = @($dirs | Where-Object { $_ -match '^[\w .\-\\]+$' } | ForEach-Object { '"' + $_.Replace('\', '\\') + '"' })
	$names = @($ClearEnv | ForEach-Object { $_.Trim() })
	$names = @($names | Where-Object { $_ -match '^[\w\-]+$' } | ForEach-Object { '"' + $_ + '"' })
	$l = $l.Replace('__RUNS__', $RunsDir).Replace('__SELF__', $self)
	return $l.Replace('__SUPPORT__', '(' + ($dirs -join ' ') + ')').Replace('__CLEARENV__', '(' + ($names -join ' ') + ')')
}

# Write the bundle and this repo's run line. $RunId '' = no run (stale entries
# still go). Load file: .bench.ini [run] load= > [bench] load= > tests/bench/acaddoc.lsp.
function Set-BenchAcadHook {
	param([string]$Main, [string]$RunId, $Ini, [string]$Root = '')
	if (-not $Root) {
		if (-not (Test-BenchWindowHost) -or -not $env:APPDATA) { return }
		$Root = "$env:APPDATA/Autodesk/ApplicationPlugins"
	}
	$b = ($Root -replace '\\', '/') + '/git-sp-bench.bundle'; $runs = "$b/Contents/runs"
	New-Item -ItemType Directory -Path $runs -Force | Out-Null
	$xml = @'
<?xml version="1.0" encoding="utf-8"?>
<ApplicationPackage SchemaVersion="1.0" AppVersion="1.0" ProductCode="{6B1C0C52-8B7E-4E44-9F3A-2E5C1B7D9A41}" UpgradeCode="{0E6F2D1A-3C4B-4A5E-8D7F-91B2C3D4E5F6}" Name="git-sp bench" Description="Loads the open git-sp bench run of each repo" Author="git-sp">
  <CompanyDetails Name="git-sp" />
  <Components>
    <RuntimeRequirements OS="Win32|Win64" Platform="AutoCAD*" SeriesMin="R19.0" />
    <ComponentEntry AppName="GitSpBench" ModuleName="./Contents/git-sp-bench.lsp" LoadOnAutoCADStartup="True" PerDocument="True" />
  </Components>
</ApplicationPackage>
'@
	$enc = New-Object System.Text.UTF8Encoding $false
	[IO.File]::WriteAllText("$b/PackageContents.xml", $xml, $enc)
	$bc = if ($Ini -and $Ini.Contains('bench')) { $Ini['bench'] } else { @{} }
	$sup = if ([string]$bc.support) { [string]$bc.support } else { 'build;menu' }
	$clr = @(([string]$bc.clearenv -split ';') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
	$lisp = Get-BenchAcadLisp -RunsDir $runs -Support $sup -ClearEnv $clr
	[IO.File]::WriteAllText("$b/Contents/git-sp-bench.lsp", $lisp, $enc)
	$line = ''
	if ($RunId) {
		$wt = Get-BenchWorktree $Main $RunId
		if (Test-Path -LiteralPath $wt) {
			$rel = ''
			if ($Ini -and $Ini.Contains($RunId)) { $rel = [string]$Ini[$RunId].load }
			if (-not $rel -and $Ini -and $Ini.Contains('bench')) { $rel = [string]$Ini['bench'].load }
			if (-not $rel) { $rel = 'tests/bench/acaddoc.lsp' }
			$lf = "$wt/$rel"; if (-not (Test-Path -LiteralPath $lf)) { $lf = '' }
			$line = ($wt -replace '/', '\') + '|' + ($lf -replace '/', '\') + '|' + ($Main -replace '/', '\')
		}
	}
	[IO.File]::WriteAllText("$runs/$(Split-Path -Leaf $Main).txt", $line, $enc)
	if ($line) {
		Write-Host "AutoCAD bench hook: $line (loaded only by an AutoCAD started with Start AutoCAD)"
	} else { Write-Host 'AutoCAD bench hook: no run; the next normal AutoCAD drawing puts the owner settings back' }
	$wtn = if ($RunId) { Get-BenchWorktree $Main $RunId } else { '' }
	$bst = if ($wtn) { Read-BenchAcadStatus "$wtn/bench-run/acad-status.txt" }
	foreach ($w in @(Get-BenchStaleWarning -Contents "$b/Contents" -Status $bst -Main $Main -RunDir $wtn -ClearEnv $clr)) {
		Write-Host "WARNING: $w"
	}
}

# Windows only: values of the [bench] clearenv names stored in the AutoCAD profile registry
# (setenv persists there). name -> value; empty off Windows or when unreadable.
function Get-BenchRegistryEnv {
	param([string[]]$Names)
	$h = @{}
	if (-not (Test-BenchWindowHost) -or -not $Names) { return $h }
	$hkey = 'HKCU:\Software\Autodesk\AutoCAD\R*\ACAD-*\FixedProfile\General'
	foreach ($k in @(Get-ChildItem $hkey -ErrorAction SilentlyContinue)) {
		foreach ($n in $Names) { $v = $k.GetValue($n); if ($v) { $h[$n] = [string]$v } }
	}
	return $h
}

# Leftovers of a bench session in the owner's AutoCAD: a list of warning lines (empty = clean).
# $Contents: the bundle's Contents folder; $Status: Read-BenchAcadStatus of the open run; $BenchRunning: a bench
# AutoCAD is running now; $EnvValues: name -> stored value (default: the registry, Windows only).
function Get-BenchStaleWarning {
	param([string]$Contents, $Status, [string]$Main, [string]$RunDir, [string[]]$ClearEnv = @(),
		[bool]$BenchRunning = $false, $EnvValues = $null)
	$out = @()
	$norm = { param($p) ([string]$p -replace '/', '\').TrimEnd('\').ToUpperInvariant() }
	$sv = "$Contents/acad-support.txt"
	if ((Test-Path -LiteralPath $sv) -and -not $BenchRunning) {
		$tail = 'the next normal AutoCAD drawing puts it back.'
		$out += "the owner's support path is still saved in $sv (a bench AutoCAD did not end cleanly): $tail"
	}
	$tv = "$Contents/acad-trusted.txt"   # plan 30 S2 / ust review Q1: the restore waits for a normal session
	if ((Test-Path -LiteralPath $tv) -and -not $BenchRunning) {
		$out += "TRUSTEDPATHS restore pending: the owner's list is saved in $tv; the next normal AutoCAD session puts it back"
	}
	if ($Status -and $Status.bench -eq 'no' -and [string]$Status['support-first'] -match '-bench-R\d{8}-\d{4}') {
		$tail = 'it loads that run, not the main clone.'
		$out += "a normal AutoCAD lists the bench folder $($Status['support-first']) first in its support path: $tail"
	}
	if ($null -eq $EnvValues) { $EnvValues = Get-BenchRegistryEnv -Names $ClearEnv }
	foreach ($n in $ClearEnv) {
		$v = [string]$EnvValues[$n]
		if ($v -and (& $norm $v) -ne (& $norm $RunDir) -and (& $norm $v) -ne (& $norm $Main) -and
			-not (& $norm $v).StartsWith((& $norm $RunDir) + '\') -and -not (& $norm $v).StartsWith((& $norm $Main) + '\')) {
			$tail = 'the next normal AutoCAD drawing clears it when it is a bench run folder.'
			$out += "the AutoCAD profile stores $n = $v, neither the open run nor the main clone: $tail"
		}
	}
	return $out
}

# Short build id of the running git-sp.ps1 (first 8 of its MD5).
function Get-BenchBuildId { return (Get-FileHash -LiteralPath $PSCommandPath -Algorithm MD5).Hash.Substring(0, 8).ToLower() }

# The main clone's copy of this script (same path under the main root) when
# it differs from the code now running ($script:BootHash): started from a run
# folder (its copy is as old as the run tag), or started from the main clone
# and the host-sync / main pull just replaced the file. $null when run from
# outside the repo, absent, unchanged, or already relaunched.
function Get-BenchMainCopy {
	param([string]$Main, [string]$StartDir)
	if ($env:GITSP_BENCH_RELAUNCHED) { return $null }
	$me = $PSCommandPath -replace '\\', '/'
	$sd = $StartDir.TrimEnd('/') + '/'
	if (-not $me.StartsWith($sd, [StringComparison]::OrdinalIgnoreCase)) { return $null }
	$other = "$Main/" + $me.Substring($sd.Length)
	if (-not (Test-Path -LiteralPath $other)) { return $null }
	if ((Get-FileHash -LiteralPath $other -Algorithm MD5).Hash -eq $script:BootHash) { return $null }
	return $other
}

# Repo hook: <main>/tools/host-sync.ps1 (no args), run with this PowerShell
# before pull and test; non-zero exit stops git-sp (test: listed + asked).
# Absent: git pull --ff-only of the main clone's branch instead (skipped when
# detached or without upstream).
function Invoke-BenchHostSync {
	param([string]$Main)
	if ($NoHostSync) { return }
	$hs = "$Main/tools/host-sync.ps1"
	if (-not (Test-Path -LiteralPath $hs)) {   # no repo hook: bring the main clone up to date (fast-forward only) so its git-sp and tools are current
		$up = Invoke-Git -AllowNonZeroExit -C $Main rev-parse --abbrev-ref --symbolic-full-name '@{u}'
		if ($LASTEXITCODE -ne 0) { return }   # detached or no upstream: leave it
		$o = Invoke-Git -AllowNonZeroExit -C $Main pull --ff-only -q
		if ($LASTEXITCODE -ne 0) { throw "git pull --ff-only in the main clone $Main failed ($(@($o) -join ' ')); -NoHostSync skips it." }
		return
	}
	$ps = (Get-Process -Id $PID).Path
	& $ps -NoProfile -ExecutionPolicy Bypass -File $hs
	if ($LASTEXITCODE -ne 0) { throw "$hs failed (exit $LASTEXITCODE). -NoHostSync skips it." }
}

# -Bench test: list problems that leave the run folder usable and ask the
# tester; -NonInteractive (or redirected input) refuses instead.
function Confirm-BenchProceed {
	param([string[]]$Issues)
	if (-not $Issues -or -not $Issues.Count) { return }
	Write-Host 'Issues found (the run folder is still usable):' -ForegroundColor Yellow
	foreach ($i in $Issues) { Write-Host "  - $i" -ForegroundColor Yellow }
	if ($NonInteractive -or [Console]::IsInputRedirected) { throw 'Stopped on the issues above (-NonInteractive).' }
	$a = Read-Host 'Proceed with run? [Y/n]'
	if ($a -match '^\s*[nN]') { throw 'Stopped by the tester.' }
}

function Invoke-BenchMain {
	param([string]$StartDir)
	$main = Get-BenchMainRoot
	$v = [string]$Verb
	# a vendored copy says when ag-toolbox has a newer git-sp
	if (-not $env:GITSP_BENCH_RELAUNCHED) {
		$vs = Get-GitSpVendorState -Dir $PSScriptRoot
		if ($vs.state -eq 'behind') {
			$vm = "git-sp: this vendored copy ($($vs.have.Substring(0, 7))) is behind $($vs.source)"
			$vm += " ($($vs.head.Substring(0, 7)))."
			Write-Host "$vm Run: git-sp -Vendor update -Commit" -ForegroundColor Yellow
		}
	}
	if ($v -eq 'test' -and -not (Test-BenchWindowHost)) { Write-Host 'the runbook window needs Windows; use -Bench push for the console form'; exit 2 }
	if ($v -in @('', 'pull')) { Invoke-BenchHostSync -Main $main }
	if ($v -eq 'test') { try { Invoke-BenchHostSync -Main $main } catch { Confirm-BenchProceed -Issues @("host-sync: $($_.Exception.Message)") } }
	$next = Get-BenchMainCopy -Main $main -StartDir $StartDir
	if ($next) {   # a run folder holds the script as of its tag: run the main clone's copy instead
		Write-Host "git-sp: running the main clone's copy $next"
		$p = @{} + $script:BenchArgs; $p['NoHostSync'] = $true
		$env:GITSP_BENCH_RELAUNCHED = '1'
		try { & $next @p } finally { Remove-Item Env:GITSP_BENCH_RELAUNCHED -ErrorAction SilentlyContinue }
		exit $LASTEXITCODE
	}
	Write-Host "git-sp build $(Get-BenchBuildId)"
	Push-Location $main
	try {
		switch ($v) {
			'push' { Invoke-BenchPush -Main $main -StartDir $StartDir }
			'delete' {
				$ini = Get-BenchIni
				$id = Resolve-BenchRunId -Main $main -StartDir $StartDir
				if (-not $id) {
					if ($NonInteractive -or [Console]::IsInputRedirected) { throw '-Bench delete needs -Run <id>.' }
					$all = @(if ($ini) { @(Get-BenchRuns $ini 'open') + @(Get-BenchRuns $ini 'results') })
					$id = @(Select-Checklist -Title 'Bench run to delete everywhere' -Items $all -Single)[0]
					if (-not $id) { return }
				}
				[void](Remove-BenchRunEverywhere -Main $main -RunId $id -Section $(if ($ini) { $ini[$id] }))
			}
			'test' {   # pull first; an error that leaves the run folder usable is listed and the tester asked
				$id = Resolve-BenchRunId -Main $main -StartDir $StartDir
				if ($id) { $script:Run = $id }
				$issues = @(); $script:BenchPicked = $null
				try { [void](Invoke-BenchPull -Main $main) } catch { $issues += "pull: $($_.Exception.Message)" }
				if (-not $script:Run) {
					$p = @($script:BenchPicked)
					if ($null -eq $script:BenchPicked) { $ini = Get-BenchIni; $p = @(Select-BenchRun -Runs $(if ($ini) { Get-BenchRuns $ini 'open' }) -Wanted '' | Where-Object { $_ }) }
					if ($p.Count -eq 0) { throw 'No open bench run.' }
					if ($p.Count -gt 1) { throw "Several open runs ($($p -join ', ')). Use -Run <id>." }
					$script:Run = $p[0]
				}
				if ($issues.Count) {
					$wt = Get-BenchWorktree $main $script:Run
					if (-not (Test-Path -LiteralPath "$wt/.git")) { throw "Run folder $wt does not exist and the pull failed: $($issues -join '; ')" }
					$tag = "bench/$($script:Run)"
					$want = Invoke-Git -AllowNonZeroExit rev-parse --verify --quiet "refs/tags/$tag^{commit}" | Select-Object -First 1
					$have = Invoke-Git -AllowNonZeroExit -C $wt rev-parse HEAD | Select-Object -First 1
					if ($want -and ([string]$want).Trim() -ne ([string]$have).Trim()) { $issues += "run folder $wt is not at $tag (HEAD $(([string]$have).Trim().Substring(0, 7)))" }
					Confirm-BenchProceed -Issues $issues
				}
				Invoke-BenchTest -Main $main -StartDir $StartDir
			}
			{ $_ -in @('', 'pull') } {
				$open = @(Invoke-BenchPull -Main $main)
				$last = @($open | Sort-Object) | Select-Object -Last 1
				Set-BenchAcadHook -Main $main -RunId $last -Ini (Get-BenchIni)
				if (-not $v) { foreach ($r in $open) { Write-Host "open run: $r" } }
			}
			default { throw "Unknown -Bench verb '$Verb' (use pull, push, test or delete)." }
		}
	} finally { Pop-Location }
}

# --- Vendoring (owner 2026-11-09): a repo carries its own copy of git-sp in bin/ -------------------------------
# bin/git-sp.vendor records where the copy came from: 'source = <git url or path>', 'ref = <branch>', 'sha = <commit>',
# 'sha256 = <git-sp.ps1 as written>'. ag-toolbox stays the source of truth; the copy is replaced whole, never edited.
$script:VendorFiles = @('bin/git-sp.ps1', 'bin/git-sp.cmd')

function Read-GitSpVendor {
	param([string]$Dir)
	$f = Join-Path $Dir 'git-sp.vendor'
	if (-not (Test-Path -LiteralPath $f)) { return $null }
	$r = @{}
	foreach ($l in @(Get-Content -LiteralPath $f)) {
		if ($l -match '^\s*(\w+)\s*=\s*(.*?)\s*$') { $r[$Matches[1]] = $Matches[2] }
	}
	return $r
}

# The source's head commit, without a prompt and with a short timeout; '' when it cannot be reached.
function Get-GitSpVendorHead {
	param([string]$Source, [string]$Branch)
	$env:GIT_TERMINAL_PROMPT = '0'
	$old = $env:GIT_SSH_COMMAND; $env:GIT_SSH_COMMAND = 'ssh -o BatchMode=yes -o ConnectTimeout=8'
	try {
		$ga = @('ls-remote', $Source, "refs/heads/$Branch")
		$o = @(Invoke-Git -AllowNonZeroExit @ga)
		if ($LASTEXITCODE -ne 0 -or -not $o.Count) { return '' }
		return (([string]$o[0]) -split '\s+')[0]
	} finally { $env:GIT_SSH_COMMAND = $old }
}

# -> @{ state = 'none' | 'current' | 'behind' | 'unknown'; have; head; source }
function Get-GitSpVendorState {
	param([string]$Dir)
	$v = Read-GitSpVendor -Dir $Dir
	if (-not $v -or -not $v.source -or -not $v.sha) { return @{ state = 'none' } }
	$b = if ($v.ref) { $v.ref } else { 'main' }
	$h = Get-GitSpVendorHead -Source $v.source -Branch $b
	$st = if (-not $h) { 'unknown' } elseif ($h -eq $v.sha) { 'current' } else { 'behind' }
	return @{ state = $st; have = $v.sha; head = $h; source = $v.source }
}

# Copy git-sp.ps1 and git-sp.cmd at <Branch> of <Source> into <Target>/bin. Fetches only those two files (shallow,
# blobless, sparse clone in a temp folder), refuses a ps1 that does not parse, writes bin/git-sp.vendor, and with
# -Commit commits the three files in the target. -> the source commit.
function Copy-GitSpVendor {
	param([string]$Source, [string]$Branch, [string]$Target, [switch]$Commit)
	$tmp = Join-Path ([IO.Path]::GetTempPath()) ('git-sp-vendor-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
	try {
		$ga = @('clone', '-q', '--depth', '1', '--filter=blob:none', '--sparse', '--branch', $Branch, $Source, $tmp)
		[void](Invoke-Git @ga)
		$ga = @('-C', $tmp, 'sparse-checkout', 'set', '--no-cone') + $script:VendorFiles
		[void](Invoke-Git @ga)
		$ga = @('-C', $tmp, 'rev-parse', 'HEAD'); $sha = (@(Invoke-Git @ga) -join '').Trim()
		foreach ($f in $script:VendorFiles) {
			if (-not (Test-Path -LiteralPath "$tmp/$f")) { throw "$Source has no $f at $Branch" }
		}
		$err = $null; [void][Management.Automation.Language.Parser]::ParseFile("$tmp/bin/git-sp.ps1", [ref]$null, [ref]$err)
		if (@($err).Count) { throw "$Source $sha bin/git-sp.ps1 does not parse: $(@($err)[0].Message)" }
		New-Item -ItemType Directory -Force -Path "$Target/bin" | Out-Null
		foreach ($f in $script:VendorFiles) { Copy-Item -LiteralPath "$tmp/$f" -Destination "$Target/$f" -Force }
		$h256 = (Get-FileHash -LiteralPath "$Target/bin/git-sp.ps1" -Algorithm SHA256).Hash
		$rec = "; git-sp vendored copy: replace it with git-sp -Vendor update, never edit it`n"
		$rec += "source = $Source`nref = $Branch`nsha = $sha`nsha256 = $h256`n"
		[IO.File]::WriteAllText("$Target/bin/git-sp.vendor", $rec)
		if ($Commit) {
			$ga = @('-C', $Target, 'add', '-f') + $script:VendorFiles + 'bin/git-sp.vendor'
			[void](Invoke-Git @ga)
			$msg = "bin/git-sp.ps1 from ag-toolbox $($sha.Substring(0, 7)) (git-sp -Vendor update)"
			$ga = @('-C', $Target, 'commit', '-q', '-m', $msg, '--') + $script:VendorFiles + 'bin/git-sp.vendor'
			[void](Invoke-Git -AllowNonZeroExit @ga)
		}
		return $sha
	} finally { Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue }
}

function Invoke-GitSpVendor {
	param([string]$RepoRoot)
	$here = $PSScriptRoot
	$rec = Read-GitSpVendor -Dir $here
	switch ([string]$Verb) {
		{ $_ -in '', 'check' } {
			$s = Get-GitSpVendorState -Dir $here
			if ($s.state -eq 'none') { Write-Host "git-sp: $here has no git-sp.vendor (this is the source copy)"; exit 0 }
			Write-Host "git-sp vendored copy: $($s.state) (have $($s.have), $($s.source) has $($s.head))"
			exit $(if ($s.state -eq 'behind') { 1 } else { 0 })
		}
		'update' {
			$tgt = if ($To) { $To } elseif ($rec) { Split-Path -Parent $here } else { '' }
			if (-not $tgt) { throw 'git-sp -Vendor update: give -To <repo root> (this is the source copy, not a vendored one).' }
			$src = if ($From) { $From } elseif ($rec -and $rec.source) { $rec.source } else {
				$ga = @('-C', $RepoRoot, 'remote', 'get-url', 'origin'); (@(Invoke-Git @ga) -join '').Trim()
			}
			$br = if ($script:BenchArgs.ContainsKey('Ref') -or -not $rec -or -not $rec.ref) { $Ref } else { $rec.ref }
			$sha = Copy-GitSpVendor -Source $src -Branch $br -Target $tgt -Commit:$Commit
			Write-Host "git-sp vendored into $([IO.Path]::GetFullPath("$tgt/bin")): $src $br $sha"
			exit 0
		}
		default { throw "Unknown -Vendor verb '$Verb' (use update or check)." }
	}
}

# --- Main ----------------------------------------------------------------

if (-not (Get-Command git -CommandType Application -ErrorAction Ignore)) {
	throw 'git was not found on PATH. Install git 2.25+ and reopen the shell.'
}

if (-not (Test-IsGitRepo)) {
	throw 'Not inside a git working tree. Run this script from within a git repository.'
}

$repoRoot = Get-GitRoot
if ($Vendor) { Invoke-GitSpVendor -RepoRoot $repoRoot }
if ($Bench) { Invoke-BenchMain -StartDir ($repoRoot -replace '\\', '/'); exit 0 }   # explicit 0: a relaunching caller reads it
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
			Set-NodeSelected -Node $node -Value $true -IncludeArchive
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
