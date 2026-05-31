# Frames
---

## Project Overview
----------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------
- This project is a repo for generic installing of files into a Parent repo.
    - This project repo will be referred to as ***Project***.
    - The parent repo will be referred to as ***Parent***
- This ***Project*** will be added as a git submodule to the ***Parent***.
- The python script for this repo is install.py with command options give in this document.

Notes:
- For the example Python class structures, I have not included the @staticmethod validation helpers.
    - The helpers must be added by the coding agent.

### The Core Concept
- We need to install an arbitary group of files into an arbitrary framework.
    - We'll call that group of files a DataGroup.
    - We'll call the frame work the Framework.
- There are multiple DataGroups.
    - These DataGroups are mutually exclusive.
    - These DataGroups are installled into the Framework specifed by FrameData.
    - Each DataGroup has a <dataGroup>.dataGroup.json file that contains information about the DataGroup.
    - That information can be found in [Data Group Config File Defintions](#data-group-config-file-definitions)
    - Each file in the DataGroup is associated with a Tag.
        - This Tag matches to a Tag in the Framework.
    - The files will be installed into the directory with the matching Tag.
    - Note, multiple files can resolve to the same Tag.
        - Therefore multiple files can be copied to the same directory.
- There is one Framework.
    - The Framework creation and Tag resolution is specified by the user in [Frame Data Config File](#frame-data-config-file-definion.)
- How it's used
    - The users should first install the Framework.
    - The user can then install DataGroups one at a time.
    - The installation of the DataGroups are mutually exclusive.
    - The user can also unintal DataGroups as needed.
    - If the user wants to uninstall the Framework, the user must uninstall all of the DataGroups.
- File Structure Example and Default setup.
    - This repo should contain the following default information.
 ```
    frameData.config.json
    exampleGroup1/
        exampleGroup.dataGroup.json
        file11.md
        file12.md
        file13.md
    exampleGroup2/
        exampleGroup2.dataGroup.json
        file21.md
        file22.md
        file23.md
    exampleGroup3/
        exampleGroup3.dataGroup.json
        file31.md
        file32.md
        file33.md
    exampleGroup4/
        exampleGroup4.dataGroup.json
        file41.md
        file42.md
        file43.md
```
`frameData.config.json`
```json
{
    "projectDirectory":"",
    "tagList":[],
    "directoryList":[        
        {"name":"sampleDirectory1", "tagList":[{{"kind":"location","name":"A"}}], "directoryList":[]},
        {"name":"sampleDirectory2", "tagList":[{{"kind":"location","name":"B"}}], "directoryList":[
            {"name":"sampleDirectory4", "tagList":[{{"kind":"location","name":"D"}}], "directoryList":[]}
        ]}],
    "dataGroupList":[
        {"name":"exampleGroup1"},
        {"name":"exampleGroup2"},
        {"name":"exampleGroup3"}.
        {"name":"exampleGroup4"}]
}
```
exampleGroup1/exampleGroupl.dataGroup.json
```json
{
    "fileList":[
        {"name":"file11.md","tag":{"kind":"location","name":"A"}, "writePolicy":"force"},
        {"name":"file12.md","tag":{"kind":"location","name":"A"}, "writePolicy":"force"},
        {"name":"file13.md","tag":{"kind":"location","name":"A"}, "writePolicy":"force"},
    ]
}
```
exampleGroup2/exampleGroup2.dataGroup.json
```json
{
    "fileList":[
        {"name":"file21.md","tag":{"kind":"location","name":"B"}, "writePolicy":"force"},
        {"name":"file22.md","tag":{"kind":"location","name":"B"}, "writePolicy":"force"},
        {"name":"file23.md","tag":{"kind":"location","name":"B"}, "writePolicy":"force"},
    ]
}
```
exampleGroup3/exampleGroup3.dataGroup.json
```json
{
    "fileList":[
        {"name":"file31.md","tag":{"kind":"location","name":"A"}, "writePolicy":"force"},
        {"name":"file32.md","tag":{"kind":"location","name":"B"}, "writePolicy":"force"},
        {"name":"file33.md","tag":{"kind":"location","name":"D"}, "writePolicy":"force"},
    ]
}
```
exampleGroup4/exampleGroup4.dataGroup.json
```json
{
    "fileList":[
        {"name":"file41.md","tag":{"kind":"location","name":"D"}, "writePolicy":"force"},
        {"name":"file42.md","tag":{"kind":"location","name":"D"}, "writePolicy":"force"},
        {"name":"file43.md","tag":{"kind":"location","name":"D"}, "writePolicy":"force"},
    ]
}
```

## File Definitions
----------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------
- There are two types of files:
    - Framework config file
    - Data Group config file
 
### Data Group Config File Definitions
----------------------------------------------------------------------------------------------------
- These are JSON files.
- The name of the files follows this pattern `<dataGroup>.dataGroup.json`
- `<dataGroup>` is a string that represents the name of the data group.
- They are located in subdirectories in this repo. 
- The locations are as follows: `/<dataGroup>/<dataGroup>.dataGroup.json`
- There is one data group config file per dataGroup directory.
- Validation Rules
    - There must be at least 1 `/<dataGroup>` directory and associated `<dataGroup>.dataGroup.json file.
    - The file must contain valid JSON. 
    - The JSON must not be malformed.
    - The config must contain all required top-level keys: fileList.
- Follow [Error Message](#error-messages) if validation fails

Example JSON:

```json
{
    "kind":"location"|"file", "name":""
    }

{
    "writePolicy":"force"|"copy"|"skip"
    }

{
    "fileList":[
        {"name":"file1.md","tag":{"kind":"location","name":"A"}, "writePolicy":"force"},
        {"name":"file2.md","tag":{"kind":"location","name":"A"}, "writePolicy":"force"},
        {"name":"file3.md","tag":{"kind":"location","name":"C"}, "writePolicy":"force"},
    ]
    }
```


#### Kind Literal Definition
------------------------------
```python
Kind = Literal["location","file"]
```
- Kind is a Literal type that specifies the category of a tag.
- Valid values: `"location"` or `"file"`

- Validation Requirements
    - The value must be one of the allowed literal values: `"location"` or `"file"`.
    - The value must be a string.
    - The value is case-sensitive.
    - The value must be present in any Tag definition.
- Follow [Error Message](#error-messages) if validation fails

#### Tag Class Definition
------------------------------

```Python
class Tag(TypeDict):
    kind: Kind
    name: str
```
##### kind
- Follow the specification in [Kind](#kind-literal-definition)

##### name
- This key specifies the name of the tag.
- Validation requirements:
    - The key must be present.
    - The value must be a non-empty string.
    - Must contain only valid identifier characters (alphanumeric and underscores).
    - Must be unique all tag.names in the project.
- Follow [Error Message](#error-messages) if validation fails

#### WritePolicy Definition
------------------------------

```python
WritePolicy = Literal["force","copy","skip"]
```
- WritePolicy is a Literal type that specifies how a file should be written to the destination.
- Valid values: `"force"`, `"copy"`, or `"skip"`
- Behavior definitions:
    - `"force"`: Overwrite the destination file if it exists.
    - `"copy"`: If the file exists in the destination, create a copy of the source file and give it an a file extention of .tmp
    - `"skip"`: Do not write the file to the destination.
- Validation Requirements
    - The value must be one of the allowed literal values: `"force"`, `"copy"`, or `"skip"`.
    - The value must be a string.
    - The value is case-sensitive.
    - The value must be present in any File definition.
    - Verify force overwrites the destination file.
    - Verify copy makes a copy of the sources file in the destination directory with a .tmp extention.
    - Verify skip cause no change to the destination directory if the destination file is present.
    - If no destination file is present, verify the source file is written to the desgination directory. 
- Follow [Error Message](#error-messages) if validation fails

#### File Class Definition
------------------------------

```python
class File(TypeDict):
    name:str
    tag:Tag
    writePolicy:WritePolicy
```

##### name
- This key is the name of the file.
- Validation requirements
    - This key must be present.
    - This value must be a non-empty string.
    - This value must be a file name in the file system.
    - Must contain only valid filename characters (no path separators like `/` or `\`).
    - Must not contain reserved characters (`<`, `>`, `:`, `"`, `|`, `?`, `*`).
    - Must not be a reserved filename (OS-dependent: `CON`, `PRN`, `AUX`, `NUL`, etc. on Windows).
    - The file must exist in the DataGroup directory.
- Follow [Error Message](#error-messages) if validation fails    

##### tag
- This key is the tag for the file.
- Validation Requirements
    - This key must be present.
    - The value must be a vaild form of the Tag class see [](#tag-class-definition)
- Follow [Error Message](#error-messages) if validation fails    

##### WritePolicy
- This key is the writepolicy for the file. 
- Validtaion Requirements
    - This key must be present.
    - This value must a vaild form of the WritePolicy Literal, See [](#writepolicy-definition)
- Follow [Error Message](#error-messages) if validation fails    

#### DataGroup Definition
------------------------------

```python
class DataGroup(TypeDict)
    fileList:list[File]
```
- 

### Frame Data Config File Definion
----------------------------------------------------------------------------------------------------
- This is a JSON file.
- It is located in the root directory of this repo.
- This file is called framedata.config.json
- The file must exist in the ***Project*** directory. 
    - If the file does not exist, the script must exit with non-zero status and print a clear error message indicating the file path that was not found.
- The file must contain valid JSON. 
    - If the JSON is malformed, the script must exit with non-zero status and print a clear error message describing the JSON parse error.
- The config must contain all required top-level keys: projectDirectory, tagList, and dataGroupLilst.
    - If any of these keys are missing, the script must exit with non-zero status and warn the user.
- If any value has an incorrect type, the script must exit with non-zero status and warn the user.

Example JSON:

```json
{
    "projectDirectory":"",
    "tagList":[],
    "directoryList":[        
        {"name":".github", "tagList":[{{"kind":"location","name":"A"}}], "directoryList":[]},
        {"name":"agents", "tagList":[{{"kind":"location","name":"C"}}], "directoryList":[]}],
    "dataGroupList":[
        {"name":""},
        {"name":""}]
}
```
#### Directory Class Definition
------------------------------
```python
class Directory(TypeDict):
    name:str
    tagList:list[Tag]
    directoryList: list[Directory]
```
##### name
- This key specifies the name of the directory.
- Validation requirements:
    - The key must be present.
    - The value must be a non-empty string.
    - Must contain only valid filename characters (no path separators or special characters that would be invalid in directory names).
    - Must be unique within its parent directoryList.
- Follow [Error Message](#error-messages) if validation fails

##### tagList Generic
- This key contains a JSON array of Tags in the directory.
- The value may be an empty array [].
- Validation requirements
    - The value must be an array.
    - Each Tag.name must be unique in the Project as specified in [Tags](#tag-class-definition)
    - Each Tag must match the structure specifed in [Tags](#tag-class-definition)
    - Each Tag defined in tagList should be referenced in dataGroup config files.
- Follow [Error Message](#error-messages) if validation fails

##### direcoryList Generic
- This key contains a JSON array of Directories in the current directory.
- The value may be an empty array [].
- Validation requirements
    - The value must be an array.
    - Each Directory must be unique in the list.
    - Each Directory must match the structure specifed in [Directory](#directory-class-definition)
    - Tags defined in tagList should be referenced in dataGroup config files and directoryList.
- Follow [Error Message](#error-messages) if validation fails

#### FrameData Class Definition
------------------------------
```python
class FrameData(TypeDict):
    projectDirectory:Path
    tagList:list[Tag]
    directoryList:list[Directory]
    dataGroupList:list[str]
```
##### projectDirectory
- This key gives the path relative to the ***Parent***.
- "" is assumed to mean the ***Parent*** directory.
- Validation requirements
    - The Key must be present.
    - No absolute paths 
    - The resolved projectDirectory path must exist. 
    - Path traversal references (e.g., ../) are not allowed. 
- Follow [Error Message](#error-messages) if validation fails

##### tagList Parent Directory
- This key contains a JSON array of Tags in the ***Parent*** directory.
- This tagList should follow the same definition and validation rules as [tagList Generic](#taglist-generic)

##### directoryList Parent Directory
- This contains a JSON array of Directories at the top of the ***Parent*** directory structure.
- This directoryList should follow the same definition and validation rules as [directoryList Generic](#direcorylist-generic)

##### dataGroupList
- This key contains a list of dataGroup names that are available for installation.
- Each entry is a string representing the name of a dataGroup directory in the ***Project***.
- Validation requirements:
  - dataGroupList must be a list of strings.
  - Each string must correspond to an existing directory in the ***Project*** with a corresponding `<value>.dataGroup.json` config file.
- Follow [Error Message](#error-messages) if validation fails

## Command Line Operations
----------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------

### Install
----------------------------------------------------------------------------------------------------

#### Install Frame
Installs the directory stucture as specified by `frameData.config.json`.
```bash 
install frame
```
#### Install DataGroup
Installs the files in the dataGroup into the directory structure.
```bash
install datagroup <dataGroup>
```
### Uninstall
----------------------------------------------------------------------------------------------------

#### Uninstall DataGroup

Uninstall the files in the dataGroup from the directory structure.
```bash
install datagroup --uninstall <dataGroup>
```

#### Uninstall DataGroup
Uninstall the directory structure as specified by `frameData.config.json`
```bash
install frame --uninstall
```
## Behaviors
----------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------

### Install Frame
----------------------------------------------------------------------------------------------------

This is behavior is initiated by [CLI Install Frame](#install-frame)

*Step*: Read frameData.config.json.
- Verify the file is correct per [frameData.config.json definition](#frame-data-config-file-definion)

*Step*: Create Directories
- Create directories per [directoryList](#directorylist-parent-directory)
- Note, the `directoryList` is a list of directories that may contain more directories.
- Situations that maybe encountered
    - No directory
        - Normal case
        - Create the directory
    - Directory Exists
        - Exception case
        - Skip creating the directory
        - Warn the user that the directory already existed.

### Uninstall Frame
----------------------------------------------------------------------------------------------------

This behavior is inititiated by [CLI Uninstall Frame](#uninstall-frame)

*Step*: Read frameData.config.json.
- Verify the file is correct per [frameData.config.json definition](#frame-data-config-file-definion)

*Step*: Remove Directories as specified.
- Note, it is expected that directories should be empty.
- If a directory is not empty, do not remove the directory.
    - Issue a warning to the user and continue on.
- Situations that maybe encountered. 
    - Directory exists and is Empty
        - Normal case
        - Just remove the directory
    - Directory exists but not Empty
        - Exception case
        - Skip removing the directory
        - Warn the users that the directory was not empty and could not be removed.
    - Directory does not exist
        - Exception case
        - Skip
        - Warn the users because it should have been there.

### Install DataGroup
----------------------------------------------------------------------------------------------------

This behavior is initiated by [CLI Install DataGroup](#install-datagroup)

*Step*: Read frameData.config.json
- Verify the file is correct.

*Step*: Read <datagroup>.dataGroup.json
- Find that file directory as specified in [Data Group Config File](#data-group-config-file-definitions)
- Verify the file is correct as specified in [Data Group Config File](#data-group-config-file-definitions)

*Step*: Determine the destination as specified in [Core Concept](#the-core-concept)

*Step*: Copy files to the target directories as specified by:
- [Data Group Config File](#data-group-config-file-definitions) and 
- [FrameData Confile Filel](#frame-data-config-file-definion)


### Uninstalll DataGroup
----------------------------------------------------------------------------------------------------

This behavior is initiated by [CLI Uninstalll DataGroup](#uninstall-datagroup)

*Step*: Read frameData.config.json
- Verify the file is correct. 

*Step*: Read <datafroup>.dataGroup.json
- Verify the file is correct.

*Step*: Determine the location of the files to be removed as specifed in D[Core Concept](#the-core-concept)

*Step*: Remove the specifed files from the Framework.
- Situatiosn that maybe encountered
    - File is present
        - Normal case
        - Remove file
    - File is not present
        - Exception case
        - Warn the user that the file to be removed is missing.



## Error Messages
- sys.exit(1) with an error message if the validation fails