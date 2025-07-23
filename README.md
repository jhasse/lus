# sly

`sly` is a task runner similar to [just](https://just.systems). It's key differentiators are:

* No DSL, `sly` uses the existing [KDL](https://kdl.dev)
* Runs tasks directly without a shell
* Comes with a simple built-in shell, so it works out-of-the-box on Windows
* Less features

```kdl
b {
    $ sly build
}

$ host="$(uname -a)"

// build main
build {
    $ cc *.a -o main
}

// test everything
test-all {
    $ sly build
    $ "./test" --all
}

// run a specific test
test {
    $ sly build
    $ "./test" --test $args
}
```
