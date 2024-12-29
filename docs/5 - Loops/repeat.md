# `repeat`
Repeats code a given number of times

## Usage
Print `Hello, World!"` to the console 5 times:
```
repeat (5) {
	output("Hello, World!");
}
```
### Output
```
Hello, World!
Hello, World!
Hello, World!
Hello, World!
Hello, World!
```

## Parameters
`repeat` expects exactly 1 parameter.
| Parameter | Type | Meaning |
|-|-|-|
| `times` | Number | The number of times to loop. If the number is a decimal, it is rounded down. |

## More Examples
Output the numbers 1-5 in order:
```
set n = 1;
repeat (5) {
	output(n);
    set n = n + 1;
}
```
### Output
```
1
2
3
4
5
```