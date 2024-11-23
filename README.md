# The heart brain project 🧠 🫀
![Illustration](https://github.com/rahulvenugopal/The-HBP/blob/main/HEP.png)

### Part 1: Get clean data
1. Load the data and select EEG channels only (in microvolts)
2. Basic filtering
3. Remove bad channels
4. Run ICA for ECG component removal
5. Reference to A1 and A2
5. Save the dataset with ECG put back to this

### Part 2: Finding R peaks and cut the data
1. Identify R peaks and add those points as a STIM channel
2. Go through the detected R peaks and create a data cleaning report
3. Epoch the data based on R peaks and have metadata saved based on sleep stages
4. Reject criteria for amplitude and flatness
5. Keep a summary of rejected epochs/channels
6. Write the epochs count per subject per sleep stage
7. Pickle the averaged HEPs

### Part 3: Statistics
1. Comparison against surrogates
2. Condition and Group comparison

### Part 4  (Data Visualisation)
1. Save the results figures for each channels and create topomaps

### Part 5: HRV analysis
1. Get the ECG channels and run Neurokit2 on it
2. Figure out continuous streaks of sleep stages (from the raw hypnogram file)
3. Create a csv sheet based on start and end of long streaks of sleep stages for ECG data

### Literature summaries for 9 papers
1. Pick 3 foundational papers on HEP
2. Pick 3 on HEP and meditation
3. Pick 3 on HEP and sleep

---
# Cardioception
![](https://raw.githubusercontent.com/embodied-computation-group/Cardioception/master/images/HeartRateDiscrimination.png)
1. Understand the [psi paper](https://www.sciencedirect.com/science/article/pii/S0042698998002855)
