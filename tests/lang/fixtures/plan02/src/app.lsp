;;; @module app
;;; @depends lib

(setq *app:state* nil)
(setq *app:state* 1)

(defun app:run (x / helper res)
  (setq helper 1)
  (setq res (lib:helper x))
  (app:local x)
  (vl-catch-all-apply 'app:local (list x))
  (mapcar '(lambda (q) (lib:helper q)) x)
  (vla-get-ActiveDocument (vlax-get-acad-object))
  (strcat "a" "b")
  (undefined-fn x)
  (lib:dup)
  (if (new_dialog "app_dlg" 1)
    (progn
      (action_tile "accept" "(app:on-ok) (done_dialog 1)")
      (start_dialog)))
  res)

(defun app:local (x) (foreach y x (princ y)))

(defun app:on-ok () (done_dialog 1))

(defun app:show ()
  (my:dcl-exec "dcl" "app_dlg"))
