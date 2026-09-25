;;; @module lib
;;; @depends core, ui
;;; @sidecar lib-notes.md

(setq *lib:count* 0 *lib:name* "x")
(setq plain 1)

(defun lib:helper (a / b)
  (setq b (+ a 1))
  b)

(defun lib:dup () 1)
(defun lib:dup () 2)

(defun C:LibCmd ()
  (lib:helper 1)
  (princ))

(defun C:log:list-vars ()
  (princ))
