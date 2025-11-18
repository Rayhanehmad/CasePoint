{ pkgs }:
{
  deps = [
    pkgs.bash
    pkgs.nodejs_20
    pkgs.python311Full
    pkgs.python311Packages.pip
  ];
}
