# `set`
Assigns a value to a variable or creates it if it doesn't exist.

## Usage
Creates a variable called `x` and assigns the number 4 to it, then output the contents of x:
```
set x = 4;
output(x);
```
### Output
```
4
```

## More Examples
Creates a variable called `x` and assigns the number 4 to it, then edits x so that it contains the string `"John"`, then output the contents of x:
```
set x = 4;
set x = "John";
output(x);
```
### Output
```
John
```

Creates a variable called `x` and assigns the number 4 to it, then increments x by 1, then output the contents of x:
```
set x = 4;
set x = x + 1;
output(x);
```
### Output
```
5
```