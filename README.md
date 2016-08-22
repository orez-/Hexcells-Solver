# Hexcells-Solver
:camera: Solver for the [Hexcells series](http://store.steampowered.com/app/265890/) - parses the screen for information and solves.
![](https://cloud.githubusercontent.com/assets/1037028/17841739/b69ccbac-67e9-11e6-8aa5-2e6449a44909.gif)

Currently only works on OS X 10.10+

#### TODOs
- Parse row-constraints from an image of the board.
- Solve non-contiguous constraints.
- Improve performance of parsing board image, maybe with numpy (currently takes a full, agonizing minute).
- Better unify existing constraint types to allow solving more subtle clues:
```
      -   -           -   -
    -   -   -       -   -   -
      1  {2}    =>    1  {2}
    -   -   -       -   x   -
      -   x           -   x
```
- Cross-platform???
