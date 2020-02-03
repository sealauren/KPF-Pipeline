KPF Data Reduction Pipeline
===========================

To install this package, you first need to download
[KeckDRPFramework](https://github.com/Keck-DataReductionPipelines/KeckDRPFramework),
as it is the only dependency that cannot be installed with `pip`

On your terminal, navigate to a (preferrably empty) project folder `MyDir`, and
clone the Framework directory

    cd MyDir
    gt clone https://github.com/Keck-DataReductionPipelines/KeckDRPFramework.git

Since `KeckDRPFramework` is still under development, it is not recommended that
you install it to your global enviroment. For now, its installation is not required
for the `KPF-Pipeline`, and simply having the package cloned is enough. Note that
the location of `KeckDRPFramework` is important: it must be in the same directory as
the `KPF-Pipeline` package.

To install, clone the repository and navigate into it

    git clone https://github.com/California-Planet-Search/KPF-Pipeline.git

Since this branch is still on develop, a github page cannot be set up yet for
the documentation. So, this branch contains the .html build of the documentaion
from sphinx. To see  the documentation,
navigate into `docs` and open `index.html` with a browswer of your choice

See the documentation for further detail, including package installation and setup.
