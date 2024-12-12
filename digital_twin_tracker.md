# Digital Twin Tracker - Pulak Mehrotra

A tracker used to both track my understanding of the topics I am implementing, as well as the results/progress of my implementations. I store all my results/code in this [Github Repository](https://github.com/ucsdwcsng/TinyTwin).

*Note:* This document contains a majority of my final findings. For a understanding of my thought process, please refer to my rough slides:
- [Wireless Slides](https://docs.google.com/presentation/d/1ZVRdaL4ylD1i6fVkltgcU_Vdj77Zs-Lg3jlwlW2bDhw/edit?usp=sharing)
- [Systems Slides](https://docs.google.com/presentation/d/15Sk_M7Azggf7XXFcFJ6bhrHNiq8MYJD5_OPluzeKJ3s/edit?usp=sharing)

## Overview

In this project, we attempt to create a cellular Digital Twin. Ushasi and I have categorized my efforts into two main areas: (1) *System Contributions* — creating a framework by building on top the existing open-source RAN stacks, and (2) *Wireless Contributions* — reducing a real-world channel into a format compatible with our Digital Twin framework.

**Summary:**
1. **System Contributions:** 
    - We have an existing OAI Implementation with the option to plug channels of our choice.
    - Summary Slides : [[Slide 1](), [Slide 2]()]
2. **Wireless Contributions:**
    - We have finalized a complete pipeline to represent a real-world, time-varying channel in a compute-intensive form that can be integrated into our existing OAI framework.
    - To summarise, I have created a short summary presentation you can refer to : [[https://ucsdcloud-my.sharepoint.com/:p:/r/personal/dbharadia_ucsd_edu/Documents/WCSNG/People/Ushasi/Tiny-twin/tiny-twin.pptx?d=w397c362b2c664ac2b1091b1ca01ee699&csf=1&web=1&e=chsHNL&nav=eyJzSWQiOjMxMSwiY0lkIjoyNDU0MDA3OTQ3fQ]() onwards]

## Time-Wise Progress

For a good estimate of a PHY channel, we have to ensure the following components are modeled/taken into account:
- Channel changes rapidly over **time** : update the channel taps periodically
- **Doppler effect**: should be taken care of by a appropriate temporal sampling of the channel
- **Spatial Aspects**: should be taken care of by simulating a MIMO system (MIMO systems are the ones mostly in use)

*Note*: MIMO is down the road, we need to get a SISO system up and running with the above two considerations first.

### Proposed Workflow

<figure align="center">
    <img src="screenshots/channel_processesing_workflow.png" alt="Channel Processing Workflow" width="500">
    <figcaption>Channel Processing Workflow</figcaption>
</figure>

More Information:
- **collectTaps()**: 
    - The overarching idea which we develop our solution on top of is we can introduce abstraction into our data transmission by convolving the input with channel taps (channel taps are simply a discretely-sampled version of the CIR of a scene).
    - We can obtain such taps from various methods and run an accurate simulation of the environment for a given instant.
    - For now, we use Sionna to get channel representations and will move on to over-the-air experiments after this.

- **selectNumberOfTaps(H,t)**: 
    - Each system, no matter how big or small, will have a limit on the amount of sliding window convolutions it can perform in real time.
    - It is reasonable to assume that the channel representation will contain a higher resolution of taps than the system supports.
    - Here, we attempt to find the most succinct representation of the channel. More information [here](https://github.com/ucsdwcsng/UCSD_Progress/blob/main/digital_twin_tracker.md#experiments-performed).

- **processTaps(H',t')**:
    - This step will only be required if the number of taps we receive is still more than our system's capacity.
    - While initially perceived as essential, the necessity of this step appears to diminish following the previous one. The reason being, if we've already invested significant effort in identifying the most dominant taps, further reduction of these taps may not be a logical progression.
    - Old version of my proposed algorithm can be found [here](https://github.com/ucsdwcsng/UCSD_Progress/blob/main/documents/processTaps.pdf).

### Fundamentals Revision

Before performing experiments, I took some time revising some old coursework and other similar materials:
- [Wireless Communications by Prof. Aditya Jagannatham](https://www.youtube.com/playlist?list=PL30blqFldQN6N0PmEPr9vFUxOY0W0omg8)
- [Excellent OFDM Notes](https://www.eit.lth.se/fileadmin/eit/courses/ettn01/HT2-2017_Rusek/OFDM_lecture_notes_161115.pdf)
- Signals and Systems by Alan V. Oppenheim (Revise)
- Wireless Communications by Andrea Goldsmith (Revise)
- ECE 257b (Upto L6)

### Experiments Performed

Experiments perfromed in Sionna using the Docker container provided by the developers. You can find my code [here](https://github.com/ucsdwcsng/TinyTwin/tree/pulak/channel).

**Hypothesis**: 
- Selecting the first few strongest channel taps will be sufficient to satisfactorily model a channel.
- *How does this make sense?* The first few taps almost always include the LoS path as well as the strongest NLoS paths. Of course, there is the chance that the taps at the end are strong as well. The point of this experiments is to see if this distortion is significant.

**Experiments**:
Done over Sionna simulations for now. Will move to over-the-air when the above-mentioned workflow is in place.

- *Part 1: What did we implement?*
    - I had a existing scene from my old work on Sionna of a Blender model of the area around my house in Bangalore.
    - After plotting the CIR and taps we realised the channel has only one dominant tap (most likely LoS).
    - The low distance between the TX-RX pair as well as the low $D_{S}$ are the likely reasons for this.
    - We dropped the ending channel taps to get a reduced representation of the channel.
    - We then attempted to plot the deviation in phase and magnitude of the convolved product $y_{\text{REDUCED}}$ compared to $y_{\text{TRUTH}}$. 
- *Part 2: Can we generalise?*  
    - We collected CIRs from a few more scenes to see if such results (single dominant tap systems) track across Sionna at the very least. We will discuss about the results below.
    - Two pre-loaded scenes from the `rt` module in Sionna were the scenes in use:
        - Munich
        - Etoile 

<figure align="center">
    <img src="screenshots/ofdm_system.png" alt="OFDM System" width="500">
    <figcaption>Setup a OFDM TX and RX in Sionna</figcaption>
</figure>


### Results

Metrics Considered:
- Moving Average of the Magnitude and Phase Difference in the convolved IQ (before decoding)
- MAPE (Mean Absolute Percentage Error) - Not of use actually. No good way to understand power differences in this case (atleast in the linear domain)

For the results, please refer to [my wireless slides](https://docs.google.com/presentation/d/1ZVRdaL4ylD1i6fVkltgcU_Vdj77Zs-Lg3jlwlW2bDhw/edit?usp=sharing) from slide 18 onwards. 
**[STILL UPLOADING PLOTS]**

### Next Steps

- See how other higher layer artifacts are affected by the changing the tap resolution.
- The next step after figuring out an appropriate tap resolution (for a given MCS) is to figure out when to update
    - Where mobility/Doppler comes into play

### TL;DR

Working on figuring an appropriate tap resolution for a given channel. Performing simulations/experiments in Sionna for now. Will move on to mobile scenarios after figuring out a succinct static channel representation.

## Systems Efforts

The best way to understand my progress in creating a ZMQ Broker that can perform real-time convolutions would be going through [my slides](https://docs.google.com/presentation/d/15Sk_M7Azggf7XXFcFJ6bhrHNiq8MYJD5_OPluzeKJ3s/edit?usp=sharing) from slide 9 onwards. A summary is below:

### GNU

If we are receiving data in the form of a stream, it might make more sense to perform sliding window convolutions on the IQ input.
- Is the data received as a stream though? --> It is not, it is receieved as blocks at the REQ sockets.
- A custom sliding window block in GNU did not give good results 
- More information on [Slides 15 and 16](https://docs.google.com/presentation/d/15Sk_M7Azggf7XXFcFJ6bhrHNiq8MYJD5_OPluzeKJ3s/edit?usp=sharing).

For more information on my initial experiments on figuring the best type of convolution to perform

### C++

As I was new to developing using ZeroMQ, I approached this step-by-step:
- First created programs that:
    - read from sockets (P1)
    - wrote to sockets (P2)
- Tried to put them together. Issues I ran into:
    - Asynchronous transmission necessitates a multi-threaded approach.
    - A data structure must store data and support multiple-thread access *at the same time.*

**New Approach [IN-PROGRESS] :**
- **Use GNU's approach to store data**
    - Effectively GNU has implemented a PUB-SUB pattern in REQ-REP.
    - For more information, refer to Slides 32-36.


## August 12th - August 20th
- Setup a [OFDM system](https://ucsdcloud-my.sharepoint.com/:p:/r/personal/dbharadia_ucsd_edu/Documents/WCSNG/People/Ushasi/Tiny-twin/tiny-twin.pptx?d=w397c362b2c664ac2b1091b1ca01ee699&csf=1&web=1&e=VI2Zs9&nav=eyJzSWQiOjI2NSwiY0lkIjo2MDM2NjI4MDZ9) in Sionna.
- Figured out how to port [our own scenes](https://github.com/ucsdwcsng/TinyTwin/blob/pulak/channel/ofdm_scenes/blr-scene-ofdm.ipynb) into Sionna using OSM -- used this to get CIRs and Channel Taps.

## August 21st - August 30th
- Started understanding the srsRAN codebase and observing how the [UE](https://github.com/ucsdwcsng/TinyTwin/blob/6c1673c12afb1e3c8e22cec523ac069eaf97a4b1/srsRAN_4G/lib/src/phy/rf/rf_zmq_imp_tx.c#L149) and [gNB's](https://github.com/ucsdwcsng/TinyTwin/blob/6c1673c12afb1e3c8e22cec523ac069eaf97a4b1/srsRAN_Project/lib/radio/zmq/radio_zmq_tx_channel.cpp#L184) ports are configured.
- Created many more such scenes in Sionna, using the pre-existing Sionna scenes: [Munich](https://github.com/ucsdwcsng/TinyTwin/blob/pulak/channel/ofdm_scenes/munich-v1-scene.ipynb) and [Etoile](https://github.com/ucsdwcsng/TinyTwin/blob/pulak/channel/ofdm_scenes/etoile-scene.ipynb).
- Started plotting [CIRs](https://github.com/ucsdwcsng/TinyTwin/tree/pulak/channel/plots/select_number_of_taps/cirs%2Bchannel_taps/tests) and [OFDM symbols](https://github.com/ucsdwcsng/TinyTwin/tree/pulak/channel/plots/select_number_of_taps/symbols/without_eq).
    - Aim was to get "good" CIRs -- Non-single tap CIRs.
    - Tried plotting [magnitude](https://github.com/ucsdwcsng/TinyTwin/tree/pulak/channel/plots/select_number_of_taps/los-etoile/power) and [phase change](https://github.com/ucsdwcsng/TinyTwin/blob/pulak/channel/plots/select_number_of_taps/los-etoile/phase/256qam.png) of OFDM output symbols for different channels.
        - **POOR METRIC**


## September 2nd - September 9th
- *Came to UCSD from India, most of the week went in setting up.*

## September 10th - September 24th
- Performed many small experiments top get the correct ZMQ ports working. More details are available from [Slide xx here]()).
- Figured out correct ZMQ port configirations -- was able to send and receive data without GRC.
- **Creating a pure C++ alternative to GRC is non-trivial.** Some components I will have to design:
    - Thread Scheduler
    - Multi-Thread Accessible Storage (RING) Buffer
    - Asynchronous Messaging System
- *Possible, but will take me time to do. Will attempt again after getting the OAI system up and running completely.*

## September 26th - November 5th
- Came up with a framework to perform Tap Reduction.
- Well documneted in slides from [here onwards](https://ucsdcloud-my.sharepoint.com/:p:/r/personal/dbharadia_ucsd_edu/Documents/WCSNG/People/Ushasi/Tiny-twin/tiny-twin.pptx?d=w397c362b2c664ac2b1091b1ca01ee699&csf=1&web=1&e=JZa8hb&nav=eyJzSWQiOjMwNSwiY0lkIjozMzIyOTQzNjUxfQ).

## November 6th - November 14th
- Plotted Delay-Doppler 

## November 15th - November 23rd
- *TRAVELLING*

## November 24th - December 1st
- Performed SVD to get path-wise delay and Doppler estimates.
- Performed Doppler Super-Resolution: Increase the FFT Size
- Plotted [more metrics](https://github.com/ucsdwcsng/TinyTwin/tree/pulak/channel/plots/when_to_update_taps/spatial/etoile-mobile) for temporal channel variation.
    - Plotted Mean Channel Power, Mean Squared Error, Earth Mover Distance and EVM.
    - EVM is still the best way to understand symbol variations.


## December 9th - Present
- Came to Phase-Shift as a good metric to model average phase shift across symbols.

### Short Term Goals - End Of Month
- Perform large-scale experiments for [tap reduction](https://ucsdcloud-my.sharepoint.com/:p:/r/personal/dbharadia_ucsd_edu/Documents/WCSNG/People/Ushasi/Tiny-twin/tiny-twin.pptx?d=w397c362b2c664ac2b1091b1ca01ee699&csf=1&web=1&e=SwZlmx&nav=eyJzSWQiOjMyNiwiY0lkIjozMTAwMDkzNzA1fQ) and [channel updation](https://ucsdcloud-my.sharepoint.com/:p:/r/personal/dbharadia_ucsd_edu/Documents/WCSNG/People/Ushasi/Tiny-twin/tiny-twin.pptx?d=w397c362b2c664ac2b1091b1ca01ee699&csf=1&web=1&e=K3PFja&nav=eyJzSWQiOjI5NCwiY0lkIjozNTI5Mzg5Mzk5fQ).
- Complete making the OAI framework.

### Next Steps:
- Discuss method to simulate temporal scenarios apart from Sionna. 
- Verify results with Ish.
- Discuss tap reduction scenarios -- what datasets/Sionna scenarios to use
- **Finish benchmarking WCSNG-24**






