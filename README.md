# los

`los` is a task runner similar to [just](https://just.systems). It's key differentiators are:

* No DSL, `los` uses the existing [KDL](https://kdl.dev)
* Runs tasks directly without a shell
* Comes with a simple built-in shell, so it works out-of-the-box on Windows
* Less features

```kdl
b {
    $ los build
}

$ host="$(uname -a)"

// build main
build {
    $ cc *.a -o main
}

// test everything
test-all {
    $ los build
    $ "./test" --all
}

// run a specific test
test {
    $ los build
    $ "./test" --test $args
}
```
