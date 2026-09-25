"""T6 AutoLISP nodes tests (S006)."""
import pytest

from graphify.extract import extract


def test_sc4_err_lsp_27_functions(tmp_path):
    """SC4: 27 distinct function nodes from err.lsp."""
    fixture_root = tmp_path / "fixtures"
    fixture_root.mkdir()
    fixture_file = fixture_root / "src_core_err.lsp"
    fixture_file.write_text(""";;;
;;; @module err
;;; @prefix err:

(defun err:_logger-ready-p (/ )
  (if *err:log-ready*
    T
    (progn
      (setq *err:log-ready*
        (and (utl:fn-defined-p 'log:add)
             (utl:fn-defined-p 'log:runtime-begin)))
      (if *err:log-ready* T nil))))

(defun err:_console (message / )
  (if message
    (progn
      (princ message)
      (princ))))

(defun err:_describe-call (fn args / fn-name arg-text)
  (setq fn-name (utl:sym-to-string fn))
  (setq arg-text (utl:str-join args ", "))
  (if (> (strlen arg-text) 0)
    (strcat fn-name "(" arg-text ")")
    (strcat fn-name "()")))

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

(defun err:_log (caller-sym is-error log-msg msg-pred / sym flag)
  (if (err:_logger-ready-p)
    (progn
      (setq sym (if (and caller-sym (= (type caller-sym) 'SYM))
                  caller-sym
                  'ERR:GENERAL))
      (setq flag (if is-error T nil))
      (vl-catch-all-apply 'log:add (list sym flag log-msg msg-pred)))))

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

(defun err:trap (caller fn args / )
  (err:_trap caller fn args nil))

(defun err:trap-desc (caller fn args description / )
  (err:_trap caller fn args description))

(defun err:safe-call (caller fn args / result)
  (setq result (err:_trap caller fn args nil))
  (if (vl-catch-all-error-p result)
    nil
    result))

(defun err:safe-call0 (caller fn-sym / result)
  (setq result
    (vl-catch-all-apply fn-sym '()))
  (if (vl-catch-all-error-p result)
    (progn
      (err:_console
        (strcat "CALL " (utl:sym-to-string fn-sym)
                " -> " (vl-catch-all-error-message result)))
      nil)
    result))

(defun err:safe-load (caller file-path / path result)
  (setq path
    (if (and (= (type file-path) 'STR) (> (strlen file-path) 0))
      (findfile file-path)
      nil))
  (cond
    ((null path)
     (err:_console
       (strcat "File not found -> " (utl:to-string file-path)))
     nil)
    (T
     (setq result
       (err:_trap caller 'load (list path) (strcat "LOAD " path)))
     (if (vl-catch-all-error-p result)
       nil
       (progn
         (err:_console (strcat "Loaded " path))
         T)))))

(defun err:_user-cancel-p (msg / upper)
  (if (and msg (= (type msg) 'STR) (> (strlen msg) 0))
    (progn
      (setq upper (strcase msg))
      (or (= upper "FUNCTION CANCELLED")
          (= upper "QUIT / EXIT ABORT")
          (wcmatch upper "*CANCEL*")
          (wcmatch upper "*QUIT*EXIT*ABORT*")))
    nil))

(defun err:make-handler (caller saved-vars undo-began cleanup-fn / old-error)
  (setq old-error *error*)
  (lambda (msg / pair var-name var-val)
    (foreach pair saved-vars
      (setq var-name (car pair))
      (setq var-val (cdr pair))
      (if (and var-name (= (type var-name) 'STR))
        (vl-catch-all-apply 'setvar (list var-name var-val))))
    (if undo-began
      (vl-catch-all-apply 'command (list "._UNDO" "_End")))
    (if (and cleanup-fn (utl:fn-defined-p cleanup-fn))
      (vl-catch-all-apply cleanup-fn '()))
    (if (not (err:_user-cancel-p msg))
      (progn
        (err:_console
          (strcat "Error in " (utl:sym-to-string caller) ": " msg))
        (err:_fire-callbacks caller msg "ERROR"))
      (err:_console (strcat "Cancelled: " msg))))
  (princ))

(defun err:with-undo (caller fn args vars / old-error handler result pair)
  (setq old-error *error*)
  (setq handler (err:make-handler caller vars T nil))
  (setq *error* handler)
  (setq result (vl-catch-all-apply fn args))
  (if (vl-catch-all-error-p result)
    (progn
      (vl-catch-all-apply 'princ (list (vl-catch-all-error-message result)))
      (setq result nil)))
  (vl-catch-all-apply 'setvar (list "*error*" old-error))
  result)

(defun err:add-callback (module fn-sym / )
  (setq *err:callbacks*
    (utl:alist-set module fn-sym *err:callbacks*))
  T)

(defun err:remove-callback (module / pair new-list found cb)
  (setq pair (assoc module *err:callbacks*))
  (if pair
    (progn
      (setq new-list (delq pair *err:callbacks*))
      (setq *err:callbacks* new-list)
      (setq found T))
    (setq found nil))
  found)

(defun err:set-debug (mode / )
  (setq *err:debug* (if mode T nil)))

(defun err:note (caller message predicate / )
  (err:_report caller nil message predicate))

(defun err:fail (caller message predicate / )
  (err:_report caller T message predicate))

(defun err:last-message (/ )
  *err:last-message*)

(defun err:clear-last-message (/ )
  (setq *err:last-message* nil))

(defun err:rethrow (err-obj / message)
  (setq message
    (cond
      ((vl-catch-all-error-p err-obj)
       (vl-catch-all-error-message err-obj))
      ((stringp err-obj) err-obj)
      (T "Unknown error")))
  message)

(defun err:load-module (key file-path / ok message)
  (err:clear-last-message)
  (setq ok (err:safe-load key file-path))
  (if ok
    (err:note key (strcat "Loaded " file-path) "PASS")
    (err:fail key (strcat "Failed to load " file-path) "FAIL"))
  ok)

(defun err:start-undo (doc / )
  (if (null doc)
    (setq doc (err:safe-call 'ERR 'vla-get-ActiveDocument
                (list (err:safe-call 'ERR 'vlax-get-acad-object nil)))))
  (if doc
    (vl-catch-all-apply 'vla-EndUndoMark (list doc))
    (vl-catch-all-apply 'vla-BeginUndoMark (list doc "AutoLISP"))))

(defun err:end-undo (doc / )
  (if doc
    (err:safe-call 'ERR 'vla-EndUndoMark (list doc))))

(defun err:with-undo-com (func / doc result)
  (setq doc (err:start-undo nil))
  (setq result (vl-catch-all-apply func nil))
  (err:end-undo doc)
  result)
""")
    paths = [fixture_file]
    result = extract(paths, root=fixture_root, cache_root=tmp_path / "cache")

    nodes = result.get("nodes", [])
    functions = [n for n in nodes if n.get("node_kind") == "function"]

    # Should have 27 function nodes
    assert len(functions) == 27, f"Expected 27 function nodes, got {len(functions)}"

    # All should have distinct ids
    ids = [n["id"] for n in functions]
    assert len(ids) == len(set(ids)), "Function ids are not distinct"


def test_sc4_command_nodes(tmp_path):
    """SC4: C:LITHP, C:LITHP-MGR, C:LITHP-INIT as command nodes."""
    fixture_root = tmp_path / "fixtures"
    fixture_root.mkdir()
    fixture_file = fixture_root / "src_core_ldr.lsp"
    fixture_file.write_text(""";;;
;;; @module ldr
;;; @prefix C:

(defun C:LITHP ()
  (princ "\nLITHP loaded.")
)

(defun C:LITHP-MGR ()
  (princ "\nLITHP Manager loaded.")
)

(defun C:LITHP-INIT ()
  (princ "\nLITHP initialized.")
)""")
    paths = [fixture_file]
    result = extract(paths, root=fixture_root, cache_root=tmp_path / "cache")

    nodes = result.get("nodes", [])
    commands = [n for n in nodes if n.get("node_kind") == "command"]

    # Should have 3 command nodes
    assert len(commands) == 3, f"Expected 3 command nodes, got {len(commands)}"

    labels = [n["label"] for n in commands]
    assert "C:LITHP" in labels
    assert "C:LITHP-MGR" in labels
    assert "C:LITHP-INIT" in labels


def test_sc4_err_trap_one_node(tmp_path):
    """SC4: err:trap is one node keeping first-seen spelling."""
    fixture_root = tmp_path / "fixtures"
    fixture_root.mkdir()
    fixture_file = fixture_root / "src_core_err.lsp"
    fixture_file.write_text(""";;;
;;; @module err
;;; @prefix err:

(defun err:trap (msg)
  (print msg)
)

(defun err:handler (code)
  (print code)
)""")
    paths = [fixture_file]
    result = extract(paths, root=fixture_root, cache_root=tmp_path / "cache")

    nodes = result.get("nodes", [])
    trap_nodes = [n for n in nodes if "trap" in n.get("label", "").lower()]

    # One function node, label err:trap (not err + trap); err:handler has no "trap".
    assert [(n["label"], n.get("node_kind")) for n in trap_nodes] == [("err:trap", "function")]


def test_sc5_function_count(tmp_path):
    """SC5: node_kind in {function, command} count matches defun count."""
    fixture_root = tmp_path / "fixtures"
    fixture_root.mkdir()
    fixture_file = fixture_root / "src_core_test.lsp"
    fixture_file.write_text("""(defun foo ()
  (print "foo")
)

(defun bar ()
  (print "bar")
)

(defun C:baz ()
  (print "baz")
)""")
    paths = [fixture_file]
    result = extract(paths, root=fixture_root, cache_root=tmp_path / "cache")

    nodes = result.get("nodes", [])
    code_nodes = [n for n in nodes if n.get("file_type") == "code"]
    function_command = [n for n in code_nodes if n.get("node_kind") in ("function", "command")]

    # 2 defun + 1 defun C: = 3 function/command nodes
    assert len(function_command) == 3, f"Expected 3 function/command nodes, got {len(function_command)}"
