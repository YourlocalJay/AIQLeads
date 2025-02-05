{pkgs}: {
  deps = [
    pkgs.python312Packages.uvicorn
    pkgs.ruff
    pkgs.python312Packages.black
    pkgs.rustc
    pkgs.pkg-config
    pkgs.openssl
    pkgs.libxcrypt
    pkgs.libiconv
    pkgs.cargo
  ];
}
