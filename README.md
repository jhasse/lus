# lus

`lus` is a task runner similar to [just](https://just.systems). It's key differentiators are:

* No DSL, `lus` uses the existing [KDL](https://kdl.dev)
* Runs tasks directly without a shell
* Comes with a simple built-in shell, so it works out-of-the-box on Windows
* Less features

```kdl
b {
    $ lus build
}

$ host="$(uname -a)"

// build main
build {
    $ cc *.a -o main
}

// test everything
test-all {
    $ lus build
    $ "./test" --all
}

// run a specific test
test {
    $ lus build
    $ "./test" --test $args
}
```
