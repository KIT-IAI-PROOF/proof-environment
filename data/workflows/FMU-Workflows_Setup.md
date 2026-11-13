# FMU Demo Workflows - how to set them up

## FMU (Functional Mock-up Unit) Demo Workflows

FMU workflows allow you to integrate external simulation models and tools into PROOF. An FMU is a standardized format for sharing simulation models.

### ConfigFmuRunner Workflow

The **ConfigFmuRunner** workflow demonstrates how to use a pre-configured FMU that accepts multiple inputs and produces outputs. This workflow uses an **Adder** FMU as an example—a simple model that sums up to three input values.

**What it does:**
- Reads input data from a file
- Passes it to the Adder FMU simulation model
- Processes and writes the results to output files

**Configuration steps:**

1. **Config FMU Runner block:** This block manages the FMU execution
   - `fmu_name`: Enter `Adder` (this must match the name defined in your *facility_param.json* located in `userdata`)

2. **CSV Column Selector block:**
   - `column_name`: Enter `sum` (selects which output column to extract)

3. **File Reader - Python block:**
   - `file_name`: Enter `adder_input.txt` (contains the input data for the FMU, already present in `userdata` directory)

4. **File Writer - Extracted block** (for processed results):
   - `file_name`: Enter a custom output filename
   - `additional_CRLF` (optional): Set to `true` to ensure the result of every step is written into a new line

5. **File Writer - Raw block** (for unprocessed results):
   - `file_name`: Enter a custom output filename
   - `additional_CRLF` (optional): Set to `true` to ensure the result of every step is written into a new line

**Output:** You'll get two files—one with extracted/processed data and one with raw simulation data.

---

### SingleFmuRunner Workflow

The **SingleFmuRunner** workflow provides more control over FMU execution. Instead of using a configuration file, you directly specify the FMU file and which inputs/outputs to use.

**What it does:**
- Loads an FMU file directly
- Allows you to define specific inputs and outputs
- Processes results through configurable file operations

**Configuration steps:**

1. **SingleFmuRunner block:**
   - `fmu_file_path`: Enter the path to your FMU file, here: `fmus/adder.fmu` (relative to `userdata`)
   - `fmu_input_list`: Specify inputs as a JSON array, here: `["input_1", "input_2", "input_3"]`
   - `fmu_output_list` (optional): Specify outputs as a JSON array, here: `["sum"]`. Must be specified to capture outputs.

2. **CSV Column Selector block:**
   - `column_name`: Enter `sum` (selects which output column to extract)

3. **File Reader - Python block:**
   - `file_name`: Enter `adder_input.txt` (contains the input data for the FMU, already present in `userdata` directory)

4. **File Writer - Extracted block:** (for processed results):
   - `file_name`: Enter your custom output filename
   - `additional_CRLF` (optional): Set to `true` to ensure the result of every step is written into a new line

5. **File Writer - Raw block:** (for unprocessed results):
   - `file_name`: Enter your custom output filename
   - `additional_CRLF` (optional): Set to `true` to ensure the result of every step is written into a new line

**Output:** Similar to ConfigFmuRunner, you'll generate both extracted and raw output files.

---

### FMU with Energy Building Model (EBM)

The **FMU-EBM** workflow combines the FMU runner with the energy building model, allowing you to integrate external FMU models into a building simulation.

**What it demonstrates:**
- Usage of FMU templates which out- and inputs are specifically designed to run with one Fmu.

**Configuration steps:**

1. **Building Block** - Sets up the physical building structure:
   - `initial_indoor_temp`: Set the starting indoor temperature (in °C)

2. **Controller Block** - Manages the heating/cooling system:
   - **Inputs**/`indoor_temp` (start value): Set the initial controller setpoint temperature (in °C)