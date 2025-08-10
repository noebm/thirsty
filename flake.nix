{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
        dependencies = with pkgs.python3Packages; [
          gpxpy
          rich
          folium
          setuptools
        ];
      in
      {
        devShells.default = pkgs.mkShell {
          name = "thirsty";
          buildInputs = dependencies;
        };

        # non forked:
        # https://github.com/jsleroy/thirsty
        # src = pkgs.fetchFromGitHub {
        #       owner = "jsleroy";
        #       repo = pname;
        #       rev = "main";
        #       hash = "sha256-TEQ4HUPCddCXHPcRlN+phn5HWhMzAJ5f7e2Icnanfds=";
        #     };
        packages.thirsty = pkgs.python3Packages.buildPythonApplication {
          pname = "thirsty";
          src = ./.;
          version = "0.1.0";
          propagatedBuildInputs =
            with pkgs.python3Packages;
            [
              commitizen
              gpxpy
              rich
              folium
            ] ++ 
              [ pkgs.pre-commit ];

          pyproject = true;
          build-system = [ pkgs.python3Packages.setuptools ];

          dontUsePytestCheck = true;
        };

        packages.default = self.packages.${system}.thirsty;
      }
    );
}
