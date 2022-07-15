# CyberGIS-HIV

**CyberGIS-HIV is a Web-based GIS application that visualizes and predicts spatiotemporal patterns of HIV rates in US counties. On the graphical user interface, users can run the model on the fly. As an output of the model, spatiotemporal patterns of estimated HIV rates and key HIV predictors are visualized via the interactive coordinated and multiple views. CyberGIS-HIV enables forecasting how future HIV rates change as HIV predictors (e.g., Pre-exposure prophylaxis (or PrEP) use rate or HIV test rate) change.**

# Getting Started

If you are interested in using CyberGIS-HIV as users ( i.e. non-experts without programming background), please follow the instruction in the section, "For Application Users". If you are interested in modifying the code and add functionalities to it, please follow instructions in the section, "For developers".

## For Application Users

Step by step instructions about how to run and use CyberGIS-HIV in [CyberGISX](https://cybergisxhub.cigi.illinois.edu) are available at [CyberGIS-HIV documentation website](https://cybergis.github.io/CyberGIS_HIV_document/build/index.html).

## For developers

For development environment, we recommend that you use CyberGISX because all the required packages have been integrated in CyberGISX.

Follow the first video at at [CyberGIS-HIV documentation website](https://cybergis.github.io/CyberGIS_HIV_document/build/index.html). It will guide you to the folder, "CyberGIS-HIV". All source codes are located in this folder. Here are the core parts of the source code.

- Adaptive_Choropleth_Mapper.py : Python main function is a starting point and contains examples of how to run with example parameter settings.
- template/Adaptive_Choropleth_Mapper.html and SAM_CONFIG.js are all HTML/JavaScript for visualizations. Adaptive_Choropleth_Mapper.py reads code in those two files and replace the variables to create the result visualization with user-defined variables.

 
### Contributors

Su Yeon Han<sup>1</sup>, Chaeyeon Han<sup>1</sup>, Chang Liu<sup>1</sup>, Jinwoo Park<sup>1</sup>, Nattapon Jaroenchai<sup>1</sup>, Zhiyu Li<sup>1</sup>, Shaowen Wang<sup>1</sup>, Bita Fayaz Farkhad<sup>2</sup>, Man-pui Sally Chan<sup>2</sup>, Danielle Sass<sup>3</sup>, Bo Li<sup>4</sup>, Dolores Albarracin<sup>2</sup>

> 1. CyberGIS Center for Advanced Digital and Spatial Studies, University of Illinois at Urbana-Champaign, Urbana, Illinois
>
> 2. University of Pennsylvania
>
> 3. Northwestern University
>
> 4. University of Illinois at Urbana-Champaign, Urbana, Illinois 

