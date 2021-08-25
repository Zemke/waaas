# Worms Armageddon as a Service

WAaaS is frontend to [zemke/docker-wa](https://github.com/zemke/wa-docker)
which allows for headless WA replay processing.

## Visualization example

Screen shot from https://cwtsite.com/games/1602

![Data visualization example](https://user-images.githubusercontent.com/3391981/81668501-0e317d00-9445-11ea-9206-954444ffd97b.png)

## Architecture on AWS

```
               o
              /|\ <----------
               |\            |
                |            |
                V            |
             Upload          | JSON response
           WAgame file       | Map file response
                |            |
                V            |
          -----------------  |
     ---->|   Lightsail   |--
    |     -----------------\
    |            |          \______________________
    |         Upload                               |
    |            |                                 |
    |            V                                 |
    |    ----------------------                    |
    |    |   S3 waaas_input   |                    | Get map file
    |    ----------------------                    |
    |            |                                 |
 Receive      Trigger                              |
  JSON           |                                 |
    |            V                                 V
    |      --------------                     -----------------------
    |      |   Lambda   |-- Upload map file ->|   S3 waaas_output   |
    |      --------------                     -----------------------
    |            |
    |          Send
    |            |
    |            V
    |       -----------
     -------|   SQS   |
            -----------
```

The S3 bucket should store the objects with a TTL.

Another S3 (i.e. `waaas_static`) could provide the static files for the web frontend
like for https://waaas.zemke.io.

## Involved entities

What's involved in this whole WAaaS thing?

- wa-docker
  - WA in a container with some convenience scripts for WA.exe's
   [CLI options](https://worms2d.info/Command-line_options)
  - There's an extension of it for running as a AWS Lambda
   triggered by S3 object upload
- AWS
  - Lambda makes this parallelizable
- Landing page
  - Describe the thing (https://waaas.zemke.io)
  - Form \*.WAgame file upload as an example
  - **Future**: Form upload immediately providing a sample visualization<sup>1</sup>
  - `cURL` example statement
  - Reference implementation from CWT, WL and WR (if it were open source)
- Python scripts
  - Extracting map
  - **Future**: Extract all kinds of things from replay<sup>2</sup>
  - Parsing log to make a JSON format for further processing

## Future

<sup>1</sup> Extract Angular implementation from CWT into it's own Angular module.

<sup>2</sup> S3 object has metadata which can be set during upload to
[extract additional information from the replay](https://worms2d.info/Command-line_options). \
Also, allow to toggle off map processing to save time when it's not needed.

