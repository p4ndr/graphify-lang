;;; @sidecar ldr.md
;;; ---------------------------------------------------------------
;;; Module Loader — ldr
;;; ---------------------------------------------------------------
;;;
;;; @doc ldr.md#C0001
;;;
;;; Depends: ver, utl, err, log, cfg
;;;
;;; @doc ldr.md#C0002
;;;
;;; ---------------------------------------------------------------

;;; ---------------------------------------------------------------
;;; Global state
;;; ---------------------------------------------------------------

(setq *ldr:loaded-modules* nil)    ;; [list] Loaded module names (strings)
(setq *ldr:module-registry* nil)   ;; [list] Alist of (name . metadata-alist)
(setq *ldr:core-loaded* nil)       ;; [boolean] T if core modules loaded
(setq *ldr:init-complete* nil)     ;; [boolean] T if full init has run

;;; ---------------------------------------------------------------
;;; Private helpers — metadata parsing
;;; ---------------------------------------------------------------

;; ldr:_parse-metadata — Parse module metadata header from a file.
;;
;; Parameters:
;;   file-path  [string]  Path to the module file.
;;
;; Returns:
;;   [list]  Alist of metadata: (("module" . name) ("version" . ver)
;;           ("prefix" . pfx) ("depends" . dep-list)
;;           ("description" . desc))
;;           nil if file has no metadata header.
;;
(defun ldr:_parse-metadata (file-path / handle line meta
                             tag-pos value dep-list trimmed)
  (if (or (null file-path) (not (findfile file-path)))
    nil
    (progn
      (setq handle (open (findfile file-path) "r"))
      (if (null handle)
        nil
        (progn
          (setq meta nil)
          ;; Read up to 30 lines looking for @tags in comments
          (repeat 30
            (if (setq line (read-line handle))
              (progn
                (setq trimmed (vl-string-trim " \t" line))
                (cond
                  ((and (> (strlen trimmed) 3)
                        (= (substr trimmed 1 2) ";;")
                        (vl-string-search "@module" trimmed))
                   (setq tag-pos (vl-string-search "@module" trimmed))
                   (setq value
                     (vl-string-trim " \t"
                       (substr trimmed (+ tag-pos 8))))
                   (if (> (strlen value) 0)
                     (setq meta
                       (cons (cons "module" value) meta))))
                  ((and (> (strlen trimmed) 3)
                        (= (substr trimmed 1 2) ";;")
                        (vl-string-search "@version" trimmed))
                   (setq tag-pos (vl-string-search "@version" trimmed))
                   (setq value
                     (vl-string-trim " \t"
                       (substr trimmed (+ tag-pos 9))))
                   (if (> (strlen value) 0)
                     (setq meta
                       (cons (cons "version" value) meta))))
                  ((and (> (strlen trimmed) 3)
                        (= (substr trimmed 1 2) ";;")
                        (vl-string-search "@prefix" trimmed))
                   (setq tag-pos (vl-string-search "@prefix" trimmed))
                   (setq value
                     (vl-string-trim " \t"
                       (substr trimmed (+ tag-pos 8))))
                   (if (> (strlen value) 0)
                     (setq meta
                       (cons (cons "prefix" value) meta))))
                  ((and (> (strlen trimmed) 3)
                        (= (substr trimmed 1 2) ";;")
                        (vl-string-search "@depends" trimmed))
                   (setq tag-pos (vl-string-search "@depends" trimmed))
                   (setq value
                     (vl-string-trim " \t"
                       (substr trimmed (+ tag-pos 9))))
                   (if (> (strlen value) 0)
                     (progn
                       ;; Split comma-separated deps and trim each
                       (setq dep-list nil)
                       (foreach d (utl:str-split value ",")
                         (setq d (vl-string-trim " \t" d))
                         (if (> (strlen d) 0)
                           (setq dep-list (cons d dep-list))))
                       (setq meta
                         (cons (cons "depends" (reverse dep-list))
                               meta)))))
                  ((and (> (strlen trimmed) 3)
                        (= (substr trimmed 1 2) ";;")
                        (vl-string-search "@description" trimmed))
                   (setq tag-pos
                     (vl-string-search "@description" trimmed))
                   (setq value
                     (vl-string-trim " \t"
                       (substr trimmed (+ tag-pos 13))))
                   (if (> (strlen value) 0)
                     (setq meta
                       (cons (cons "description" value) meta))))))))
          (close handle)
          (if meta (reverse meta) nil))))))

;; ldr:_resolve-path — Find the file path for a module.
;;
;; Parameters:
;;   mod-name  [string]  Module name.
;;
;; Returns:
;;   [string]  Full path to module file, or nil if not found.
;;
(defun ldr:_resolve-path (mod-name / root mod-dir mod-file)
  (setq root (cfg:get-framework-root))
  (if root
    (progn
      ;; Try src/modules/<name>/mod.lsp
      (setq mod-dir (strcat root "src\\modules\\" mod-name "\\"))
      (setq mod-file (strcat mod-dir "mod.lsp"))
      (if (findfile mod-file)
        mod-file
        ;; Try src/plugins/<name>.lsp
        (progn
          (setq mod-file (strcat root "src\\plugins\\" mod-name ".lsp"))
          (if (findfile mod-file)
            mod-file
            nil))))
    nil))

;;; ---------------------------------------------------------------
;;; Private helpers — dependency resolution
;;; ---------------------------------------------------------------

;; ldr:_resolve-deps — Topological sort with circular dependency detection.
;;
;; Parameters:
;;   mod-name  [string]  Module name to resolve.
;;   visited   [list]    List of module names already in the resolution chain.
;;
;; Returns:
;;   [list]  Ordered list of module names to load (dependencies first).
;;           nil if circular dependency detected.
;;
;; @doc ldr.md#C0003
;;
(defun ldr:_resolve-deps (mod-name visited / meta deps dep order
                           sub-order found-cycle d)
  ;; Check for circular dependency
  (if (member mod-name visited)
    (progn
      (err:_report 'LDR T
        (strcat "Circular dependency detected: "
                (utl:str-join (reverse (cons mod-name visited)) " -> "))
        "DEPS")
      nil)
    (progn
      ;; Already loaded — no deps needed
      (if (ldr:loaded-p mod-name)
        (list mod-name)
        (progn
          ;; Look up metadata for dependencies
          (setq meta (cdr (assoc mod-name *ldr:module-registry*)))
          (setq deps
            (if meta
              (cdr (assoc "depends" meta))
              nil))
          (setq order nil)
          (setq found-cycle nil)
          ;; Resolve each dependency recursively
          (foreach dep deps
            (if (and (not found-cycle)
                     (not (ldr:loaded-p dep)))
              (progn
                (setq sub-order
                  (ldr:_resolve-deps dep
                    (cons mod-name visited)))
                (if sub-order
                  ;; Append resolved deps, avoiding duplicates
                  (foreach d sub-order
                    (if (not (member d order))
                      (setq order
                        (reverse (cons d (reverse order))))))
                  (setq found-cycle T)))))
          (if found-cycle
            nil
            ;; Add self at the end
            (if (not (member mod-name order))
              (reverse (cons mod-name (reverse order)))
              order)))))))

;; ldr:_load-core — Load core modules in dependency order.
;;
;; Returns:
;;   [boolean]  T if all core modules loaded successfully.
;;
;; @doc ldr.md#C0004
;;
(defun ldr:_load-core (/ root core-files pair path all-ok file-name)
  (setq root (cfg:get-framework-root))
  (if (null root)
    (progn
      (err:_report 'LDR T "Framework root not found." "INIT")
      nil)
    (progn
      (setq core-files
        (list
          (cons "ver" "ver.lsp")
          (cons "utl" "utl.lsp")
          (cons "err" "err.lsp")
          (cons "log" "log.lsp")
          (cons "cfg" "cfg.lsp")
          (cons "dtk" "dtk.lsp")))
      (setq all-ok T)
      (foreach pair core-files
        (setq file-name (cdr pair))
        (setq path (strcat root "src\\core\\" file-name))
        (if (not (findfile path))
          ;; Try findfile with just the name (supports AutoCAD search paths)
          (setq path (findfile file-name)))
        (if path
          (progn
            (if (not (ldr:loaded-p (car pair)))
              (progn
                (if (err:safe-load 'LDR path)
                  (progn
                    (setq *ldr:loaded-modules*
                      (reverse
                        (cons (car pair)
                              (reverse *ldr:loaded-modules*))))
                    (err:note 'LDR
                      (strcat "Core loaded: " (car pair)) "INIT"))
                  (progn
                    (err:_report 'LDR T
                      (strcat "Failed to load core: " (car pair))
                      "INIT")
                    (setq all-ok nil))))))
          (progn
            (err:_report 'LDR T
              (strcat "Core file not found: " file-name) "INIT")
            (setq all-ok nil))))
      (setq *ldr:core-loaded* all-ok)
      all-ok)))

;;; ---------------------------------------------------------------
;;; Public API
;;; ---------------------------------------------------------------

;; ldr:init — Run the complete framework initialisation.
;;
;; Parameters: none
;;
;; Returns:
;;   [boolean]  T if all core modules loaded successfully.
;;
;; @doc ldr.md#C0005
;;
(defun ldr:init (/ ok mod-name mode)
  (if *ldr:init-complete*
    (progn
      (err:note 'LDR "Framework already initialised." "INIT")
      T)
    (progn
      ;; Ensure Visual LISP extensions
      (if (and (boundp 'vl-load-com)
               (utl:fn-defined-p 'vl-load-com))
        (vl-load-com))
      ;; Detect version
      (if (utl:fn-defined-p 'ver:init)
        (ver:init))
      ;; Load core modules
      (setq ok (ldr:_load-core))
      (if (not ok)
        (progn
          (err:_report 'LDR T
            "Core module loading failed." "INIT")
          nil)
        (progn
          ;; Initialise configuration
          (if (utl:fn-defined-p 'cfg:init)
            (cfg:init nil))
          ;; Initialise logging
          (if (utl:fn-defined-p 'log:init)
            (progn
              (log:init
                (list
                  (cons "verbose" (cfg:get-bool "general" "log-verbose"))
                  (cons "to-console"
                    (cfg:get-bool "debug" "log-to-console"))))
              (log:runtime-begin 'LITHP)))
          ;; Discover modules
          (ldr:discover)
          ;; Load auto modules
          (foreach mod-name
            (mapcar 'car (cdr (assoc "modules" *cfg:data*)))
            (setq mode (cfg:get-module-mode mod-name))
            (if (= mode "auto")
              (ldr:require mod-name)))
          ;; Mark init complete
          (setq *ldr:init-complete* T)
          (err:note 'LDR "Framework initialisation complete." "INIT")
          T)))))

;; ldr:require — Load a module if not already loaded.
;;
;; Parameters:
;;   mod-name  [string]  Module name (e.g. "layer-tools").
;;
;; Returns:
;;   [boolean]  T if module is loaded (or was already loaded).
;;
;; @doc ldr.md#C0006
;;
(defun ldr:require (mod-name / load-order path ok dep meta)
  (if (ldr:loaded-p mod-name)
    T
    (progn
      ;; Ensure module is in registry
      (if (not (assoc mod-name *ldr:module-registry*))
        (progn
          ;; Try to find and register
          (setq path (ldr:_resolve-path mod-name))
          (if path
            (progn
              (setq meta (ldr:_parse-metadata path))
              (if meta
                (setq *ldr:module-registry*
                  (cons (cons mod-name meta) *ldr:module-registry*))))
            (progn
              (err:_report 'LDR T
                (strcat "Module not found: " mod-name) "LOAD")
              (setq path nil)))))
      ;; Resolve load order
      (setq load-order (ldr:_resolve-deps mod-name nil))
      (if (null load-order)
        nil
        (progn
          (setq ok T)
          (foreach dep load-order
            (if (and ok (not (ldr:loaded-p dep)))
              (progn
                (setq path (ldr:_resolve-path dep))
                (if (null path)
                  (progn
                    (err:_report 'LDR T
                      (strcat "Dependency not found: " dep) "LOAD")
                    (setq ok nil))
                  (if (err:safe-load 'LDR path)
                    (progn
                      (setq *ldr:loaded-modules*
                        (reverse
                          (cons dep
                                (reverse *ldr:loaded-modules*))))
                      (err:note 'LDR
                        (strcat "Module loaded: " dep) "LOAD"))
                    (progn
                      (err:_report 'LDR T
                        (strcat "Failed to load: " dep) "LOAD")
                      (setq ok nil)))))))
          ok)))))

;; ldr:unload — Unload a module from the framework.
;;
;; Parameters:
;;   mod-name  [string]  Module name to unload.
;;
;; Returns:
;;   [boolean]  T if unloaded.
;;
;; @doc ldr.md#C0007
;;
(defun ldr:unload (mod-name / cleanup-fn new-list item meta deps
                    dep-meta dep-deps blocked-by)
  (if (not (ldr:loaded-p mod-name))
    (progn
      (err:note 'LDR
        (strcat "Module not loaded: " mod-name) "UNLOAD")
      nil)
    (progn
      ;; Check if other loaded modules depend on this one
      (setq blocked-by nil)
      (foreach item *ldr:loaded-modules*
        (if (and (/= item mod-name)
                 (setq dep-meta
                   (cdr (assoc item *ldr:module-registry*))))
          (progn
            (setq dep-deps (cdr (assoc "depends" dep-meta)))
            (if (member mod-name dep-deps)
              (setq blocked-by
                (cons item blocked-by))))))
      (if blocked-by
        (progn
          (err:_report 'LDR T
            (strcat "Cannot unload " mod-name
                    " — required by: "
                    (utl:str-join (reverse blocked-by) ", "))
            "UNLOAD")
          nil)
        (progn
          ;; Call cleanup function if defined
          (setq meta (cdr (assoc mod-name *ldr:module-registry*)))
          (if meta
            (progn
              (setq cleanup-fn
                (read (strcat
                  (cdr (assoc "prefix" meta)) "cleanup")))
              (if (utl:fn-defined-p cleanup-fn)
                (err:safe-call0 'LDR cleanup-fn))))
          ;; Remove from loaded list
          (setq new-list nil)
          (foreach item *ldr:loaded-modules*
            (if (/= item mod-name)
              (setq new-list (cons item new-list))))
          (setq *ldr:loaded-modules* (reverse new-list))
          (err:note 'LDR
            (strcat "Module unloaded: " mod-name) "UNLOAD")
          T)))))

;; ldr:loaded-p — Check if a module is currently loaded.
;;
;; Parameters:
;;   mod-name  [string]  Module name.
;;
;; Returns:
;;   [boolean]  T if loaded.
;;
(defun ldr:loaded-p (mod-name / )
  (if (member mod-name *ldr:loaded-modules*) T nil))

;; ldr:discover — Scan src/modules/ and src/plugins/ for available modules.
;;
;; Returns:
;;   [list]  List of module metadata alists.
;;
;; @doc ldr.md#C0008
;;
(defun ldr:discover (/ root mod-dir plug-dir subdirs dir mod-file
                      meta name entries file-list file path)
  (setq root (cfg:get-framework-root))
  (if (null root)
    nil
    (progn
      (setq entries nil)
      ;; Scan src/modules/
      (setq mod-dir (strcat root "src\\modules\\"))
      (if (vl-file-directory-p mod-dir)
        (progn
          (setq subdirs
            (vl-catch-all-apply 'vl-directory-files
              (list mod-dir nil -1)))
          (if (and subdirs (not (vl-catch-all-error-p subdirs)))
            (foreach dir subdirs
              (if (and (/= dir ".") (/= dir ".."))
                (progn
                  (setq mod-file
                    (strcat mod-dir dir "\\mod.lsp"))
                  (if (findfile mod-file)
                    (progn
                      (setq meta (ldr:_parse-metadata mod-file))
                      (if meta
                        (progn
                          (setq name
                            (cdr (assoc "module" meta)))
                          (if (and name
                                   (not (assoc name entries)))
                            (setq entries
                              (cons (cons name meta) entries)))))))))))))
      ;; Scan src/plugins/
      (setq plug-dir (strcat root "src\\plugins\\"))
      (if (vl-file-directory-p plug-dir)
        (progn
          (setq file-list
            (vl-catch-all-apply 'vl-directory-files
              (list plug-dir "*.lsp" 1)))
          (if (and file-list (not (vl-catch-all-error-p file-list)))
            (foreach file file-list
              (setq path (strcat plug-dir file))
              (setq meta (ldr:_parse-metadata path))
              (if meta
                (progn
                  (setq name (cdr (assoc "module" meta)))
                  (if (and name (not (assoc name entries)))
                    (setq entries
                      (cons (cons name meta) entries)))))))))
      ;; Update registry
      (setq *ldr:module-registry* (reverse entries))
      *ldr:module-registry*)))

;; ldr:list-modules — List all discovered modules with their load status.
;;
;; Returns:
;;   [list]  List of (name version status depends) tuples.
;;
(defun ldr:list-modules (/ result entry name meta version status depends)
  (setq result nil)
  (foreach entry *ldr:module-registry*
    (setq name (car entry))
    (setq meta (cdr entry))
    (setq version (cdr (assoc "version" meta)))
    (setq status
      (if (ldr:loaded-p name) "loaded" "available"))
    (setq depends (cdr (assoc "depends" meta)))
    (setq result
      (cons (list name
              (if version version "?")
              status
              (if depends depends nil))
            result)))
  (reverse result))

;;; ---------------------------------------------------------------
;;; Command entry points
;;; ---------------------------------------------------------------

;; C:LITHP-INIT — Full framework initialisation command.
(defun C:LITHP-INIT (/ )
  (ldr:init)
  (princ))

;; C:LITHP-MGR — Open the manager UI.
(defun C:LITHP-MGR (/ )
  (if (not *ldr:init-complete*) (ldr:init))
  (if (utl:fn-defined-p 'mgr:show)
    (mgr:show)
    (progn
      (err:_report 'LDR T "Manager UI not loaded." "INIT")
      (princ "\nManager UI not available.")))
  (princ))

;; C:LITHP — Alias for LITHP-INIT.
(defun C:LITHP (/ )
  (C:LITHP-INIT))

;;; ---------------------------------------------------------------
;;; Test entry point
;;; ---------------------------------------------------------------

;; ldr:test-all — Run all loader tests.
;;
;; @doc ldr.md#C0009
;;

(princ)
