# Syntax
## Functions
Every function follows this structure:
```
function(parameters);
```
- The parameters are separated by commas (`,`)
- Every function ends with a semicolon (`;`)

## Keywords
Every keyword has a different structure, but they all share things in common:
  - The keyword is the first part of a statement
  - Every keyword statement ends with a semicolon (`;`)

## Loops
Every loop follows this structure:
```
loop (parameters) {
	...
}
```

## Other things to note
- Whitespace between tokens should not affect execution:
	- These code blocks should all run the same: 
      ```
      output("Hello,");
      output("World!");
      ```
      ```
      output("Hello,"); output("World!");
      ```
      ```
      output    
      (        "Hello,")
      ;
             output

             ( "World!"   )    ;
      ```