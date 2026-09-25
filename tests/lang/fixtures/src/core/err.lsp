;;; @sidecar err.md
;;; ---------------------------------------------------------------
;;; Error Handling Module — err
;;; ---------------------------------------------------------------
;;;
;;; @doc err.md#C0001
;;;
;;; Depends: ver, utl
;;;
;;; ---------------------------------------------------------------

;;; ---------------------------------------------------------------
;;; Global state
;;; ---------------------------------------------------------------

(setq *err:debug* nil)          ;; [boolean] Debug mode toggle (default nil)
(setq *err:last-message* nil)   ;; [string] Last error message
(setq *err:log-ready* nil)      ;; [boolean] Whether logger is available
(setq *err:callbacks* nil)      ;; [list] Error event callbacks ((module . fn-symbol) ...)
(setq *err:saved-vars* nil)     ;; [list] System variable stack for nested error handlers

;;; ---------------------------------------------------------------
;;; Private helpers
;;; ---------------------------------------------------------------

;; err:_logger-ready-p — Check if the logger is available by capability.
;;
;; Returns:
;;   [boolean]  T if log:add is a defined function.
;;
;; @doc err.md#C0002
;;
(defun err:_logger-ready-p (/ )
  (if *err:log-ready*
    T
    (progn
      (setq *err:log-ready*
        (and (utl:fn-defined-p 'log:add)
             (utl:fn-defined-p 'log:runtime-begin)))
      (if *err:log-ready* T nil))))

;; err:_console — Print a message to the console.
(defun err:_console (message / )
  (if message
    (progn
      (princ message)
      (princ))))

;; err:_describe-call — Build a human-readable call description.
(defun err:_describe-call (fn args / fn-name arg-text)
  (setq fn-name (utl:sym-to-string fn))
  (setq arg-text (utl:str-join args ", "))
  (if (> (strlen arg-text) 0)
    (strcat fn-name "(" arg-text ")")
    (strcat fn-name "()")))

;; err:_fire-callbacks — Fire all registered error callbacks.
;;
;; Parameters:
;;   caller   [symbol]  Module that triggered the error.
;;   message  [string]  Error message.
;;   pred     [string]  Predicate/category tag.
;;
(defun err:_fire-callbacks (caller message pred / pair fn-sym result)
  (foreach pair *err:callbacks*
    (setq fn-sym (cdr pair))
    (if (utl:fn-defined-p fn-sym)
      (progn
        (setq result
          (vl-catch-all-apply fn-sym (list caller message pred)))
        (if (vl-catch-all-error-p result)
          (err:_console
            (strcat "\n[ERR] Callback error: "
                    (vl-catch-all-error-message result))))))))

;; err:_log — Log a message via the logging module if available.
;;
;; Parameters:
;;   caller-sym  [symbol]   Calling module identifier.
;;   is-error    [boolean]  T for error, nil for info.
;;   log-msg     [string]   Message text.
;;   msg-pred    [string]   Category predicate.
;;
(defun err:_log (caller-sym is-error log-msg msg-pred / sym flag)
  (if (err:_logger-ready-p)
    (progn
      (setq sym (if (and caller-sym (= (type caller-sym) 'SYM))
                  caller-sym
                  'ERR:GENERAL))
      (setq flag (if is-error T nil))
      (vl-catch-all-apply 'log:add (list sym flag log-msg msg-pred)))))

;; err:_report — Report an error or info message.
;;
;; Parameters:
;;   caller-sym  [symbol]   Calling module identifier.
;;   is-error    [boolean]  T for error, nil for info.
;;   message     [string]   Message text.
;;   predicate   [string]   Category predicate.
;;
;; Returns:
;;   [string]  The message.
;;
(defun err:_report (caller-sym is-error message predicate / prefix sym)
  (setq sym (if (and caller-sym (= (type caller-sym) 'SYM))
              caller-sym
              'ERR:GENERAL))
  (setq prefix (if is-error "[ERROR]" "[INFO]"))
  (if is-error
    (setq *err:last-message* message))
  (if (or *err:debug* is-error)
    (err:_console
      (strcat "\n" prefix " " (utl:sym-to-string sym) " -> " message)))
  (err:_log sym is-error message predicate)
  (if is-error
    (err:_fire-callbacks sym message predicate))
  message)

;;; ---------------------------------------------------------------
;;; Public API — trap wrappers
;;; ---------------------------------------------------------------

;; err:_trap — Internal trap implementation with optional description.
;;
;; Parameters:
;;   caller       [symbol]  Calling module identifier.
;;   fn           [symbol]  Function to call.
;;   args         [list]    Arguments to pass.
;;   description  [string]  Custom description (nil for auto).
;;
;; Returns:
;;   [any]  Function return value on success, error object on failure.
;;
(defun err:_trap (caller fn args description / result message full)
  (setq result (vl-catch-all-apply fn args))
  (if (vl-catch-all-error-p result)
    (progn
      (setq message (vl-catch-all-error-message result))
      (setq full
        (if description
          (strcat description " -> " message)
          (strcat (err:_describe-call fn args) " -> " message)))
      (err:_report caller T full "FAIL")))
  result)

;; err:trap — Wrap a function call with error trapping.
;;
;; Parameters:
;;   caller  [symbol]  Symbol identifying the calling module (for logging).
;;   fn      [symbol]  Function to call.
;;   args    [list]    Arguments to pass to fn.
;;
;; Returns:
;;   [any]  The function's return value on success, or the error object on failure.
;;
;; Side effects:
;;   On error: logs message, sets *err:last-message*, fires error callbacks.
;;
;; @doc err.md#C0003
;;
(defun err:trap (caller fn args / )
  (err:_trap caller fn args nil))

;; err:trap-desc — Wrap a function call with a custom error description.
;;
;; Parameters:
;;   caller       [symbol]  Calling module identifier.
;;   fn           [symbol]  Function to call.
;;   args         [list]    Arguments to pass.
;;   description  [string]  Custom description for error messages.
;;
;; Returns:
;;   [any]  Return value or error object.
;;
(defun err:trap-desc (caller fn args description / )
  (err:_trap caller fn args description))

;; err:safe-call — Wrap a function call; return nil on error.
;;
;; Parameters:
;;   caller  [symbol]  Calling module identifier.
;;   fn      [symbol]  Function to call.
;;   args    [list]    Arguments to pass.
;;
;; Returns:
;;   [any]  Return value on success, nil on error.
;;
(defun err:safe-call (caller fn args / result)
  (setq result (err:_trap caller fn args nil))
  (if (vl-catch-all-error-p result)
    nil
    result))

;; err:safe-call0 — Call a no-argument function safely.
;;
;; Parameters:
;;   caller  [symbol]  Calling module identifier.
;;   fn-sym  [symbol]  Function symbol to call.
;;
;; Returns:
;;   [any]  Return value on success, nil on error.
;;
;; @doc err.md#C0004
;;
(defun err:safe-call0 (caller fn-sym / result)
  (setq result
    (vl-catch-all-apply fn-sym '()))
  (if (vl-catch-all-error-p result)
    (progn
      (err:_report caller T
        (strcat "CALL " (utl:sym-to-string fn-sym)
                " -> " (vl-catch-all-error-message result))
        "FAIL")
      nil)
    result))

;; err:safe-load — Load a file with error trapping and reporting.
;;
;; Parameters:
;;   caller     [symbol]  Calling module identifier.
;;   file-path  [string]  Path to the file to load.
;;
;; Returns:
;;   [boolean]  T on success, nil on failure.
;;
(defun err:safe-load (caller file-path / path result)
  (setq path
    (if (and (= (type file-path) 'STR) (> (strlen file-path) 0))
      (findfile file-path)
      nil))
  (cond
    ((null path)
     (err:_report caller T
       (strcat "File not found -> " (utl:to-string file-path))
       "FAIL")
     nil)
    (T
     (setq result
       (err:_trap caller 'load (list path) (strcat "LOAD " path)))
     (if (vl-catch-all-error-p result)
       nil
       (progn
         (err:_report caller nil (strcat "Loaded " path) "PASS")
         T)))))

;;; ---------------------------------------------------------------
;;; Public API — *error* handler
;;; ---------------------------------------------------------------

;; err:_user-cancel-p — Check if a message is a user-cancel string.
;;
;; Parameters:
;;   msg  [string]  Error message to check.
;;
;; Returns:
;;   [boolean]  T if msg is a cancel/abort message.
;;
(defun err:_user-cancel-p (msg / upper)
  (if (and msg (= (type msg) 'STR) (> (strlen msg) 0))
    (progn
      (setq upper (strcase msg))
      (or (= upper "FUNCTION CANCELLED")
          (= upper "QUIT / EXIT ABORT")
          (wcmatch upper "*CANCEL*")
          (wcmatch upper "*QUIT*EXIT*ABORT*")))
    nil))

;; err:make-handler — Create a custom *error* handler that restores state.
;;
;; Parameters:
;;   caller      [symbol]  Calling module identifier.
;;   saved-vars  [list]    Alist of (var-name . saved-value) for system variables.
;;   undo-began  [boolean] T if UNDO _Begin was issued (will issue UNDO _End on error).
;;   cleanup-fn  [symbol]  Optional function to call for additional cleanup (nil = none).
;;
;; Returns:
;;   [function]  An *error* handler function.
;;
;; @doc err.md#C0005
;;
(defun err:make-handler (caller saved-vars undo-began cleanup-fn / old-error)
  (setq old-error *error*)
  (lambda (msg / pair var-name var-val)
    ;; 1. Restore system variables
    (foreach pair saved-vars
      (setq var-name (car pair))
      (setq var-val (cdr pair))
      (if (and var-name (= (type var-name) 'STR))
        (vl-catch-all-apply 'setvar (list var-name var-val))))
    ;; 2. Issue UNDO _End if needed
    (if undo-began
      (vl-catch-all-apply 'command (list "._UNDO" "_End")))
    ;; 3. Call cleanup function if provided
    (if (and cleanup-fn (utl:fn-defined-p cleanup-fn))
      (vl-catch-all-apply cleanup-fn '()))
    ;; 4-5. Log and fire callbacks (skip for user-cancel)
    (if (not (err:_user-cancel-p msg))
      (progn
        (err:_report caller T
          (strcat "Error in " (utl:sym-to-string caller) ": " msg)
          "ERROR")
        (err:_fire-callbacks caller msg "ERROR"))
      ;; Still log cancel messages at info level
      (err:_log caller nil (strcat "Cancelled: " msg) "CANCEL"))
    ;; 7. Restore previous handler
    (setq *error* old-error)
    (princ)))

;; err:with-undo — Execute a function wrapped in UNDO begin/end with error protection.
;;
;; Parameters:
;;   caller  [symbol]  Calling module identifier.
;;   fn      [symbol]  Function to call.
;;   args    [list]    Arguments to pass.
;;   vars    [list]    System variables to save/restore: (("OSMODE" . value) ...).
;;
;; Returns:
;;   [any]  Function return value, or nil on error.
;;
;; @doc err.md#C0006
;;
(defun err:with-undo (caller fn args vars / old-error handler result pair)
  (setq old-error *error*)
  (setq handler (err:make-handler caller vars T nil))
  (setq *error* handler)
  (command "._UNDO" "_Begin")
  (setq result (vl-catch-all-apply fn args))
  (command "._UNDO" "_End")
  ;; Restore system variables on success too
  (foreach pair vars
    (if (and (car pair) (= (type (car pair)) 'STR))
      (vl-catch-all-apply 'setvar (list (car pair) (cdr pair)))))
  (setq *error* old-error)
  (if (vl-catch-all-error-p result)
    (progn
      (err:_report caller T
        (strcat (utl:sym-to-string fn) " -> "
                (vl-catch-all-error-message result))
        "FAIL")
      nil)
    result))

;;; ---------------------------------------------------------------
;;; Public API — error events
;;; ---------------------------------------------------------------

;; err:add-callback — Register a callback function for error events.
;;
;; Parameters:
;;   module   [symbol]  Module identifier for the callback.
;;   fn-sym   [symbol]  Function to call on error. Receives (caller message predicate).
;;
;; Returns:
;;   [boolean]  T on success.
;;
;; @doc err.md#C0007
;;
(defun err:add-callback (module fn-sym / )
  (setq *err:callbacks*
    (utl:alist-set module fn-sym *err:callbacks*))
  T)

;; err:remove-callback — Remove a registered error callback.
;;
;; Parameters:
;;   module  [symbol]  Module identifier.
;;
;; Returns:
;;   [boolean]  T if removed, nil if not found.
;;
(defun err:remove-callback (module / pair new-list found cb)
  (setq pair (assoc module *err:callbacks*))
  (if pair
    (progn
      (setq new-list nil)
      (setq found nil)
      (foreach cb *err:callbacks*
        (if (not (equal cb pair))
          (setq new-list (cons cb new-list))
          (setq found T)))
      (setq *err:callbacks* (reverse new-list))
      found)
    nil))

;;; ---------------------------------------------------------------
;;; Public API — debug mode
;;; ---------------------------------------------------------------

;; err:set-debug — Set the debug mode toggle.
;;
;; Parameters:
;;   mode  [boolean]  T for verbose debug output, nil for silent logging.
;;
(defun err:set-debug (mode / )
  (setq *err:debug* (if mode T nil)))

;;; ---------------------------------------------------------------
;;; Public API — convenience
;;; ---------------------------------------------------------------

;; err:note — Log an informational message.
;;
;; Parameters:
;;   caller     [symbol]  Calling module identifier.
;;   message    [string]  Message text.
;;   predicate  [string]  Category tag.
;;
;; Returns:
;;   [string]  The message.
;;
(defun err:note (caller message predicate / )
  (err:_report caller nil message predicate))

;; err:fail — Log an error message.
;;
;; Parameters:
;;   caller     [symbol]  Calling module identifier.
;;   message    [string]  Message text.
;;   predicate  [string]  Category tag.
;;
;; Returns:
;;   [string]  The message.
;;
(defun err:fail (caller message predicate / )
  (err:_report caller T message predicate))

;; err:last-message — Return the last error message.
;;
;; Returns:
;;   [string|nil]  Last error message, or nil if none.
;;
(defun err:last-message (/ )
  *err:last-message*)

;; err:clear-last-message — Clear the last error message.
;;
;; Returns:
;;   nil
;;
(defun err:clear-last-message (/ )
  (setq *err:last-message* nil))

;; err:rethrow — Re-report an error object.
;;
;; Parameters:
;;   err-obj  [any]  An error object from vl-catch-all-apply, or a string.
;;
;; Returns:
;;   [string]  The error message.
;;
(defun err:rethrow (err-obj / message)
  (setq message
    (cond
      ((vl-catch-all-error-p err-obj)
       (vl-catch-all-error-message err-obj))
      ((null err-obj) nil)
      (T (utl:to-string err-obj))))
  (if (or (null message) (= message ""))
    (setq message "Unhandled error"))
  (err:_report 'ERR:RETHROW T message "FAIL")
  message)

;; err:load-module — Load a module file with error tracking.
;;
;; Parameters:
;;   key        [symbol]  Module identifier symbol.
;;   file-path  [string]  Path to the file to load.
;;
;; Returns:
;;   [list]  (key nil) on success, (key error-message) on failure.
;;
(defun err:load-module (key file-path / ok message)
  (err:clear-last-message)
  (setq ok (err:safe-load key file-path))
  (if ok
    (progn
      (if (= (type key) 'SYM)
        (set key (findfile file-path)))
      (list key nil))
    (progn
      (setq message (or (err:last-message) "LOAD-FAILED"))
      (if (null (findfile file-path))
        (setq message "FILE-NOT-FOUND"))
      (list key message))))

;;; ---------------------------------------------------------------
;;; Public API — undo group manager (COM-based)
;;; ---------------------------------------------------------------

;; err:start-undo — Begin an undo group.
;;
;; Parameters:
;;   doc  [vla-object|nil]  Document object. If nil, uses active document.
;;
;; Returns:
;;   [vla-object]  The document object used (for passing to err:end-undo).
;;
(defun err:start-undo (doc / )
  (if (null doc)
    (setq doc (err:safe-call 'ERR 'vla-get-ActiveDocument
                (list (err:safe-call 'ERR 'vlax-get-acad-object nil)))))
  (if doc
    (err:safe-call 'ERR 'vla-StartUndoMark (list doc)))
  doc)

;; err:end-undo — End an undo group.
;;
;; Parameters:
;;   doc  [vla-object]  Document object (from err:start-undo).
;;
(defun err:end-undo (doc / )
  (if doc
    (err:safe-call 'ERR 'vla-EndUndoMark (list doc))))

;; err:with-undo-com — Execute a function within a COM undo group.
;;
;; Parameters:
;;   func  [symbol|function]  Function to call (no arguments).
;;
;; Returns:
;;   [any]  Result of func, or nil on error (undo group still closed).
;;
;; @doc err.md#C0008
;;
(defun err:with-undo-com (func / doc result)
  (setq doc (err:start-undo nil))
  (setq result (vl-catch-all-apply func nil))
  (err:end-undo doc)
  (if (vl-catch-all-error-p result)
    (progn
      (log:add 'ERR nil
        (strcat "Undo group error: "
                (vl-catch-all-error-message result))
        "ERROR")
      nil)
    result))

;;; ---------------------------------------------------------------
;;; Test entry point
;;; ---------------------------------------------------------------

;; err:test-all — Run all error handling tests.
;;
;; @doc err.md#C0009
;;

(princ)
