# CHANGELOG

<!-- version list -->

## v1.3.0 (2026-06-02)

### Bug Fixes

- `ruff` was not found when the application was launched from gnome.
  ([`b82ec95`](https://github.com/wxgeo/ptyx-mcq-editor/commit/b82ec950f74fc51728452bda0581a9db3db6e2d9))

- Exercise menu items were inverted.
  ([`c0f556f`](https://github.com/wxgeo/ptyx-mcq-editor/commit/c0f556fd76dc1c48650f88d210fcf7c7af6c6b24))

- Settings index function should support docs too, and not only paths.
  ([`c002bea`](https://github.com/wxgeo/ptyx-mcq-editor/commit/c002beacaa2d03488af9a3f9490d31a0c1d3c041))

### Features

- Ability to add temporary bookmarks in the editor's margin.
  ([`2455f47`](https://github.com/wxgeo/ptyx-mcq-editor/commit/2455f479b3bd59c1862ad34c6b92452078135ab3))

- Add tools for autocompletion (not enable yet, needs more work).
  ([`84eae4c`](https://github.com/wxgeo/ptyx-mcq-editor/commit/84eae4c7b2c65498d9c7827c56f0ceb529788387))

- Basic help for pTyX tags.
  ([`c45e989`](https://github.com/wxgeo/ptyx-mcq-editor/commit/c45e9890af2257a40fcc32a4c29ceb5eef8e63cf))

- Better error windows.
  ([`df48ca5`](https://github.com/wxgeo/ptyx-mcq-editor/commit/df48ca5d4dea5f446b69dc739905f84e607e134e))

- Implement autocompletion for LaTeX commands and pTyX tags.
  ([`cecd208`](https://github.com/wxgeo/ptyx-mcq-editor/commit/cecd2080fd43dca7522c0b02f7ab9145ae82f4d7))

- Implement autocompletion for Python code.
  ([`7da7ade`](https://github.com/wxgeo/ptyx-mcq-editor/commit/7da7ade68f4b00479f50f4b705ed617902f40fec))

- Improve readibility of the function signature in the help window.
  ([`88d6ee6`](https://github.com/wxgeo/ptyx-mcq-editor/commit/88d6ee66327495afe4b3dba47c672585865712d4))

- Much better help in the editor for python objects.
  ([`a97b8ef`](https://github.com/wxgeo/ptyx-mcq-editor/commit/a97b8ef170e85042b4a1abf6d4337e464c40285e))

- Nicest info tooltip when pressing F1.
  ([`7dad5a7`](https://github.com/wxgeo/ptyx-mcq-editor/commit/7dad5a7412eaaf88f0347af50e5ed4a3ccddbee1))

- Show docstring when pressing F1.
  ([`62f5d17`](https://github.com/wxgeo/ptyx-mcq-editor/commit/62f5d177a4eb37d29a021f4802d251866d64e6ec))

### Refactoring

- Modernize python code.
  ([`d1c6109`](https://github.com/wxgeo/ptyx-mcq-editor/commit/d1c6109e94ac342a4f340fac56e457adcc31cbb9))

- New package for custom widgets.
  ([`cf205e2`](https://github.com/wxgeo/ptyx-mcq-editor/commit/cf205e27dc62b2d8d3d2fe830da2dad371b0a974))


## v1.2.0 (2026-03-22)

### Features

- The main menu content adapts now to the type of the edited file.
  ([`4f54c5f`](https://github.com/wxgeo/ptyx-mcq-editor/commit/4f54c5ff9e9e502bcb832114322be27e2f60a67d))


## v1.1.1 (2026-03-15)

### Bug Fixes

- Always parse the whole editor content, to ensure a correct syntax highlighting.
  ([`90abbe9`](https://github.com/wxgeo/ptyx-mcq-editor/commit/90abbe9fe65ac1b5373c94594b75901144e7658f))

- Don't try to generate a config file for non-mcq pTyX files.
  ([`d9d2f58`](https://github.com/wxgeo/ptyx-mcq-editor/commit/d9d2f581e583a8abdfb24bd94edf4fdad7813709))


## v1.1.0 (2025-11-15)

### Bug Fixes

- Always refesh the indicator concerning students ids' file.
  ([`8163981`](https://github.com/wxgeo/ptyx-mcq-editor/commit/816398140d70e32bbcb1954c1be284c858c6d3d0))

- Ptyx-mcq version in `pyproject.toml`.
  ([`cba50e8`](https://github.com/wxgeo/ptyx-mcq-editor/commit/cba50e827a1ec3b63b35701a866f256bcbc723ef))

### Features

- Add facilities in the editor for the students csv file gestion.
  ([`5e05888`](https://github.com/wxgeo/ptyx-mcq-editor/commit/5e05888cb8a091ea99b599a70edf53637267fceb))

- Display python error in editor when hovering corresponding line.
  ([`d8bde0f`](https://github.com/wxgeo/ptyx-mcq-editor/commit/d8bde0fec5cdb9096e71c240541e8b65d2677b16))

- New command line argument: --install-shortcuts.
  ([`537aa55`](https://github.com/wxgeo/ptyx-mcq-editor/commit/537aa55cfd48167b563518c16e31a5ea96f1aefe))

### Refactoring

- Indicators' gestion rewritten.
  ([`347b2a7`](https://github.com/wxgeo/ptyx-mcq-editor/commit/347b2a7a210131b90d4c0e5274e7b519e160be95))

- New module for indicator handlers.
  ([`fc3076e`](https://github.com/wxgeo/ptyx-mcq-editor/commit/fc3076e662e228a59338d4ca033ef05bfc8155b9))


## v1.0.0 (2025-10-30)

- Initial Release
