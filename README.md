# CourseAnalysis
Analysis of fell race routes based on the data available through fellrunner.org.uk


## How it works

The project is split in to 3 different parts
1. Scraping race data off of www.fellrunner.org.uk
2. Fit a model to that data using the idea of a *standard runner*
3. Fit another model to estimate race duration from the course vital statistics


## Getting hold of the data

All data comes from fellrunner website, with *a lot* of manual cleanup.

More to be written here when I have some more time.


## Fitting the standard runner model

Imagine a robot-like fell runner who can bang out completely consistent race performances day after day after day.
If he runs the same course 100 days in a row he will get 100 identical results. He is consistently good/bad over all
distances and terrain. This imaginary *standard runner* is the benchmark that we are going to measure all courses
and all other runners against.

For every course the standard runner has a finish time. We might not know what it is yet, but it does exist, call it t_course.

For every other competitor the standard runner will either be some amount faster or some amount slower, call it k_runner.

So if I am scored 10% slower than the standard runner then I will expect to finish 10% slower for every single race route.

If the number of races is M, and then number of unique runners is N then there are total of M + N model parameters that we
need to fit to minimise the sum of the errors between the runners' predicted finish times and the actual finish times.

Where a runner's predicted finish time is t_runner = t_course * k_runner


## Fitting a model to predict t_course based on the vital statistics

Each race route has a couple of vital statistics: distance and climb.
More climb means that the average pace will slow down, but by how much?
More distance means that the average pace will slow down, again by how much?

The original intent behind all of this was to figure out how much each foot of climb costs compared with distance on
the flat (eg 1000ft is the equivalent of adding an extra 1.5 miles to the course).

The whole *gnarliness* thing was a bit of fun to explain away the difference between the predicted race duration
(based on distance and ascent) and the actual race duration (based on the t_course parameter that we fit in the first model).


## Problems with the modelling

There are a number of things that aren't done so well
* If different people have the same name, the results will get confused
* Runners are assigned a single score for their entire race career - there is no accounting for peaks and troughs in race form
* Any individual race 'gnarliness' is heavily influenced by the accuracy of course measurements. On average the model will predict reasonably well, but for specific races an under-reported race distance will swamp any other factors.
