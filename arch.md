# Architecture

## Simple Interactive Control for a Single DF

## Selection

## Reactive loop

In the signal callback, refresh the rendering

* compute the dependent computations on the selection df again
  * we have to capture the dependent computation, for now we are just going to seek the user's help, where they will have a function that takes in the dependent DF and generate the new DF.

* pass this via the python <widget_name>.update
