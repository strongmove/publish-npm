#!/usr/bin/env python

from pathlib import Path
import subprocess
import json

CWF = Path(__file__)
CWD = CWF.resolve().parent
PACKAGE_DOT_JSON_PATH = CWD / "package.json"
TSCONFIG_DOT_JSON_PATH = CWD / "tsconfig.json"
ROLLUP_CONFIG_FILENAME = "rollup.config.js"
ROLLUP_CONFIG_PATH = CWD / ROLLUP_CONFIG_FILENAME
ROLLUP_CONFIG_TEXT = """// Reference: https://dev.to/alexeagleson/how-to-create-and-publish-a-react-component-library-2oe
// Action: Move react to peerDependencies from devDependencies
import resolve from "@rollup/plugin-node-resolve";
import commonjs from "@rollup/plugin-commonjs";
import typescript from "@rollup/plugin-typescript";
import postcss from "rollup-plugin-postcss";
import dts from "rollup-plugin-dts";
import { terser } from "rollup-plugin-terser";
import peerDepsExternal from "rollup-plugin-peer-deps-external";

const packageJson = require("./package.json");

const inputDir = "src";
const inputFileBase = "entry";
const inputFile = `${inputFileBase}.ts`;

const config = [
  {
    input: `${inputDir}/${inputFile}`,
    output: [
      {
        file: packageJson.main,
        format: "cjs",
        sourcemap: true,
      },
      {
        file: packageJson.module,
        format: "esm",
        sourcemap: true,
      },
    ],
    plugins: [
      peerDepsExternal(),
      resolve(),
      commonjs(),
      typescript({ tsconfig: "./tsconfig.json" }),
      postcss(),
      terser(),
    ],
  },
  {
    input: `dist/esm/types/${inputFileBase}.d.ts`,
    output: [{ file: packageJson.types, format: "esm" }],
    plugins: [dts()],
    external: [/\.css$/],
  },
];
export default config;"""


def create_rollup_config():
    def save_default_rollup_config():
        with open(ROLLUP_CONFIG_PATH, "w") as f:
            f.write(ROLLUP_CONFIG_TEXT)

    if not ROLLUP_CONFIG_PATH.exists():
        save_default_rollup_config()
    else:
        overwrite = input(f"ROLLUP_CONFIG_PATH already exists. Overwrite? (y/N)")
        if overwrite.lower() == "y":
            save_default_rollup_config()
        else:
            print("Exiting without overwrite.")


def install_required_npm_packages():
    command = "npm install rollup @rollup/plugin-node-resolve @rollup/plugin-typescript @rollup/plugin-commonjs rollup-plugin-dts rollup-plugin-postcss rollup-plugin-peer-deps-external rollup-plugin-terser @babel/core @babel/preset-env @babel/preset-react @babel/preset-typescript babel-jest --save-dev"
    subprocess.check_call(command, shell=True)


def fix_package_dot_json():
    def add_rollup_script(package):
        package["scripts"]["rollup"] = "rollup -c"
        return package

    def add_publish_script(package):
        package["scripts"]["pub"] = "rollup -c && npm publish"
        return package

    def add_project_paths(package):
        package["main"] = "dist/cjs/index.js"
        package["module"] = "dist/esm/index.js"
        package["files"] = ["dist"]
        package["types"] = "dist/index.d.ts"
        return package

    def make_public(package):
        package["private"] = False
        return package

    def add_github_info(package, github_name, repo_name):
        package["name"] = f"@{github_name}/{repo_name}"
        package["publishConfig"] = {
            "registry": f"https://npm.pkg.github.com/{github_name}"
        }
        return package

    with open(PACKAGE_DOT_JSON_PATH, "r") as f:
        package = json.loads(f.read())
    package = add_rollup_script(package)
    package = add_publish_script(package)
    github_name = input("What is your github username? ")
    repo_name = input("What is the repository name? ")
    package = add_github_info(package, github_name, repo_name)
    package = add_project_paths(package)
    package = make_public(package)
    with open(PACKAGE_DOT_JSON_PATH, "w") as f:
        f.write(json.dumps(package, indent=2))


def fix_tsconfig_dot_json():
    with open(TSCONFIG_DOT_JSON_PATH, "r") as f:
        config = json.loads(f.read())
    new_compiler_options = {
        "jsx": "react-jsx",
        "module": "ESNext",
        "declaration": True,
        "declarationDir": "types",
        "sourceMap": True,
        "outDir": "dist",
        "moduleResolution": "node",
        "allowSyntheticDefaultImports": True,
        "emitDeclarationOnly": True,
        "noEmit": False,
    }
    config["compilerOptions"].update(new_compiler_options)
    with open(TSCONFIG_DOT_JSON_PATH, "w") as f:
        f.write(json.dumps(config, indent=2))


def main():
    create_rollup_config()
    install_required_npm_packages()
    fix_package_dot_json()
    fix_tsconfig_dot_json()


if __name__ == "__main__":
    import doctest

    doctest.testmod()
    main()
