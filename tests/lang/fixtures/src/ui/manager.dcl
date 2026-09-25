/* AutoLITHP Module Manager — Phase 4 full DCL */

lithp_mgr : dialog {
  label = "AutoLITHP Module Manager";
  children_alignment = left;
  fixed_width = true;
  width = 72;
  : column {
    : boxed_column {
      label = "Modules";
      : list_box {
        key = "lbxModules";
        height = 14;
        width = 68;
        multiple_select = false;
      }
    }
    : boxed_column {
      label = "Module Details";
      : row {
        : text {
          key = "lblName";
          label = "Name:";
          width = 6;
        }
        : text {
          key = "txtModName";
          value = "";
          width = 20;
        }
        : text {
          key = "lblVer";
          label = "Version:";
          width = 8;
        }
        : text {
          key = "txtModVer";
          value = "";
          width = 10;
        }
        : text {
          key = "lblStatus";
          label = "Status:";
          width = 7;
        }
        : text {
          key = "txtModStatus";
          value = "";
          width = 15;
        }
      }
    }
    : row {
      : button {
        key = "btnEnable";
        label = "Enable";
        width = 8;
        fixed_width = true;
      }
      : button {
        key = "btnDisable";
        label = "Disable";
        width = 8;
        fixed_width = true;
      }
      : button {
        key = "btnLoad";
        label = "Load";
        width = 8;
        fixed_width = true;
      }
      : button {
        key = "btnUnload";
        label = "Unload";
        width = 8;
        fixed_width = true;
      }
      : spacer { width = 2; }
      : button {
        key = "btnImport";
        label = "Import...";
        width = 10;
        fixed_width = true;
      }
      : button {
        key = "btnAlias";
        label = "Aliases";
        width = 8;
        fixed_width = true;
      }
    }
    : row {
      : button {
        key = "btnViewLog";
        label = "View Log";
        width = 10;
        fixed_width = true;
      }
      : spacer { width = 38; }
      : button {
        key = "btnClose";
        label = "Close";
        width = 10;
        fixed_width = true;
        is_cancel = true;
      }
    }
    : boxed_column {
      label = "Info";
      : text {
        key = "txtInfo";
        value = "Select a module to view details.";
        width = 68;
      }
    }
  }
}
