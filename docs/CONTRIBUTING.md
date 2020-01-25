# Contributing
Thank you very much for considering to contribute to out project. devolo Home Control is a complex system, that covers a lot of use cases. Nevertheless we could think about use cases it does not cover and didn't want to wait for those use cases to be covered. Other projects have those use cases and having the possibility to integrate devolo Home Control into those project is our goal. To achieve that goal, help is welcome.

The following guidelines will help you to understand how you can help. They will also help you respecting our time to manage and develop this open source project. In return, we will reciprocate that respect in addressing your issues, assessing changes, and helping you finalize your pull requests.

## Table of contents
1. [Reporting an issue](#reporting-an-issue)
1. [Requesting a feature](#requesting-a-feature)
1. [Code style guide](#code-style-guide)

## Reporting an issue
If you are having issues with our module, especially, if you found a bug, we want to know. Please [create an issue](https://github.com/2Fake/devolo_home_control_api/issues). However, you should keep in mind that it might take some time for us to respond to your issue. We will try to get in contact with you within 2 weeks. Please also respond within 2 weeks, if we have further inquiries.

## Requesting a feature
While we develop this module, we have our own use cases in mind. Those use cases do not necessarily meet your use cases. Nevertheless we want to hear about them, so you can either [create an issue](https://github.com/2Fake/devolo_home_control_api/issues) or create a merge request. By choosing the first way, you tell us to take care about your use case. That will take time as we will priorities it with our own needs. By choosing the second way, you can speed up this process. Please read our code style guide.

## Code style guide
We basically follow [PEP8](https://www.python.org/dev/peps/pep-0008/), but deviate in some points for - as we think - good reasons. If you have good reasons to stick strictly to PEP8 or even have good reasons to deviate from our deviation, feel free to convince us.

We limit out lines to 120 characters, as that is maximum length still allowing code reviews without horizontal scrolling.

As PEP8 allows to use extra blank lines sparingly to separate groups of related functions, we use an extra line between static methods and constructor, constructor and properties, properties and public methods, and public methods and internal methods.

We use double string quotes, except when the string contains double string quotes itself or when used as key of a dictionary.

If you find code where we violated our own rules, feel free to [tell us](https://github.com/2Fake/devolo_home_control_api/issues).