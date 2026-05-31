# Frames
---

## Project Overview
----------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------
- This project is a repo for installing files into a Parent repo in a generic way.
    - This project repo will be referred to as ***Project***.
    - The parent repo will be referred to as ***Parent***
- This ***Project*** will be added as a git submodule to the ***Parent***.
- This repo provides an `install` command, with command options defined in this document.

Notes:
- For the example Python class structures, I have not included the @staticmethod validation helpers.
    - The helpers must be added by the coding agent.

### The Core Concept
- We need to install an arbitrary group of files into an arbitrary framework.
    - We'll call that group of files a DataGroup.
    - We'll call the framework the Framework.
- There are multiple DataGroups.
    - These DataGroups can coexist in the same Framework.
    - These DataGroups should not interfere with each other unless a file rule explicitly allows it.
    - These DataGroups are installed into the Framework specified by FrameData.
    - Each DataGroup has a <dataGroup>.dataGroup.json file that contains information about the DataGroup.
    - That information can be found in [Data Group Config File Definitions](#data-group-config-file-definitions)
    - Each file in the DataGroup is associated with a Tag.
        - This Tag matches to a Tag in the Framework.
    - The files will be installed into the directory with the matching Tag.
    - Note, multiple files can resolve to the same Tag.
        - Therefore multiple files can be copied to the same directory.
- There is one Framework.
    - The Framework creation and Tag resolution are specified by the user in [Frame Data Config File Definition](#frame-data-config-file-definition)
- How it's used
    - The users should first install the Framework.
    - The user can then install DataGroups one at a time or over time as needed.
    - Multiple DataGroups can be installed at the same time.
    - The user can also uninstall DataGroups as needed.
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
        {"name":"sampleDirectory1", "tagList":[{"kind":"location","name":"A"}], "directoryList":[]},
        {"name":"sampleDirectory2", "tagList":[{"kind":"location","name":"B"}], "directoryList":[
            {"name":"sampleDirectory4", "tagList":[{"kind":"location","name":"D"}], "directoryList":[]}
        ]}
    ],
    "dataGroupList":["exampleGroup1", "exampleGroup2", "exampleGroup3", "exampleGroup4"]
}
```
exampleGroup1/exampleGroup1.dataGroup.json
```json
{
    "fileList":[
        {"name":"file11.md","tag":{"kind":"location","name":"A"}, "writePolicy":"force"},
        {"name":"file12.md","tag":{"kind":"location","name":"A"}, "writePolicy":"force"},
        {"name":"file13.md","tag":{"kind":"location","name":"A"}, "writePolicy":"force"}
    ]
}
```
exampleGroup2/exampleGroup2.dataGroup.json
```json
{
    "fileList":[
        {"name":"file21.md","tag":{"kind":"location","name":"B"}, "writePolicy":"force"},
        {"name":"file22.md","tag":{"kind":"location","name":"B"}, "writePolicy":"force"},
        {"name":"file23.md","tag":{"kind":"location","name":"B"}, "writePolicy":"force"}
    ]
}
```
exampleGroup3/exampleGroup3.dataGroup.json
```json
{
    "fileList":[
        {"name":"file31.md","tag":{"kind":"location","name":"A"}, "writePolicy":"force"},
        {"name":"file32.md","tag":{"kind":"location","name":"B"}, "writePolicy":"force"},
        {"name":"file33.md","tag":{"kind":"location","name":"D"}, "writePolicy":"force"}
    ]
}
```
exampleGroup4/exampleGroup4.dataGroup.json
```json
{
    "fileList":[
        {"name":"file41.md","tag":{"kind":"location","name":"D"}, "writePolicy":"force"},
        {"name":"file42.md","tag":{"kind":"location","name":"D"}, "writePolicy":"force"},
        {"name":"file43.md","tag":{"kind":"location","name":"D"}, "writePolicy":"force"}
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
    - If a requested `<dataGroup>` directory does not exist, report the missing directory in the error message.
    - If `/<dataGroup>/<dataGroup>.dataGroup.json` does not exist for a discovered or requested dataGroup, report the missing config file in the error message.
    - If `fileList` exists but is not an array, report that type mismatch in the error message.
    - If `fileList` is an empty array, report that a DataGroup must contain at least one file in the error message.
    - If two entries in `fileList` use the same `name`, report the duplicate file entry in the error message.
- Follow [Error Message](#error-messages) if validation fails

Example JSON fragments:

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
class Tag(TypedDict):
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
    - Must be unique across all `Tag.name` values in the project.
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
    - Verify `copy` makes a copy of the source file in the destination directory with a `.tmp` extension.
    - Verify `skip` causes no change to the destination directory if the destination file is present.
    - If no destination file is present, verify the source file is written to the destination directory.
- Follow [Error Message](#error-messages) if validation fails

#### File Class Definition
------------------------------

```python
class File(TypedDict):
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
    - The value must be a valid form of the Tag class. See [Tag Class Definition](#tag-class-definition)
    - The referenced Tag must exist exactly once in FrameData.
    - If the Tag cannot be resolved in FrameData, the script must exit with non-zero status and print a clear error message identifying the file and unresolved Tag.
- Follow [Error Message](#error-messages) if validation fails    

##### WritePolicy
- This key is the writepolicy for the file. 
- Validation Requirements
    - This key must be present.
    - This value must be a valid form of the WritePolicy Literal. See [WritePolicy Definition](#writepolicy-definition)
- Follow [Error Message](#error-messages) if validation fails    

#### DataGroup Definition
------------------------------

```python
class DataGroup(TypedDict):
    fileList:list[File]
```
- Represents the contents of one `<dataGroup>.dataGroup.json` file.

### Frame Data Config File Definition
----------------------------------------------------------------------------------------------------
- This is a JSON file.
- It is located in the root directory of this repo.
- This file is called `frameData.config.json`.
- The file must exist in the ***Project*** directory. 
    - If the file does not exist, the script must exit with non-zero status and print a clear error message indicating the file path that was not found.
- The file must contain valid JSON. 
    - If the JSON is malformed, the script must exit with non-zero status and print a clear error message describing the JSON parse error.
- The config must contain all required top-level keys: projectDirectory, tagList, directoryList, and dataGroupList.
    - If any of these keys are missing, the script must exit with non-zero status and warn the user.
- If any value has an incorrect type, the script must exit with non-zero status and warn the user.
- If `directoryList` is missing, the script must exit with non-zero status and print a clear error message because it is a required top-level key.
- If `dataGroupList` contains duplicate names, the script must exit with non-zero status and print a clear error message identifying the duplicate dataGroup entry.
- If any dataGroup listed in `dataGroupList` does not have a matching directory and `/<dataGroup>/<dataGroup>.dataGroup.json` file in the Project, the script must exit with non-zero status and print a clear error message identifying the missing resource.

Example JSON:

```json
{
    "projectDirectory":"",
    "tagList":[],
    "directoryList":[        
        {"name":".github", "tagList":[{"kind":"location","name":"A"}], "directoryList":[]},
        {"name":"agents", "tagList":[{"kind":"location","name":"C"}], "directoryList":[]}
    ],
    "dataGroupList":["exampleGroup1", "exampleGroup2"]
}
```
#### Directory Class Definition
------------------------------
```python
class Directory(TypedDict):
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
    - Each Tag must match the structure specified in [Tag Class Definition](#tag-class-definition)
    - Each Tag defined in tagList should be referenced in dataGroup config files.
- Follow [Error Message](#error-messages) if validation fails

##### directoryList Generic
- This key contains a JSON array of Directories in the current directory.
- The value may be an empty array [].
- Validation requirements
    - The value must be an array.
    - Each Directory must be unique in the list.
    - Each Directory must match the structure specified in [Directory Class Definition](#directory-class-definition)
    - Tags defined in tagList should be referenced in dataGroup config files and directoryList.
- Follow [Error Message](#error-messages) if validation fails

#### FrameData Class Definition
------------------------------
```python
class FrameData(TypedDict):
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
- This directoryList should follow the same definition and validation rules as [directoryList Generic](#directorylist-generic)
- If two resolved directory paths are the same after combining parent and child names, the script must exit with non-zero status and print a clear error message identifying the conflicting directories.
- If a path that must be created as a directory already exists as a file, the script must exit with non-zero status and print a clear error message identifying the path conflict.

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
Installs the directory structure as specified by `frameData.config.json`.
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

#### Uninstall Frame
Uninstall the directory structure as specified by `frameData.config.json`
```bash
install frame --uninstall
```
## Behaviors
----------------------------------------------------------------------------------------------------
----------------------------------------------------------------------------------------------------

### Install Frame
----------------------------------------------------------------------------------------------------

This behavior is initiated by [CLI Install Frame](#install-frame)

*Step*: Read frameData.config.json.
- Verify the file is correct per [frameData.config.json definition](#frame-data-config-file-definition)

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
    - A file exists at the target directory path
        - Exception case
        - Exit with non-zero status.
        - Print a clear error message identifying the conflicting file path.
    - The process does not have permission to create a directory
        - Exception case
        - Exit with non-zero status.
        - Print a clear error message identifying the directory path that could not be created.

### Uninstall Frame
----------------------------------------------------------------------------------------------------

This behavior is initiated by [CLI Uninstall Frame](#uninstall-frame)

*Step*: Read frameData.config.json.
- Verify the file is correct per [frameData.config.json definition](#frame-data-config-file-definition)

*Step*: Remove Directories as specified.
- Note, it is expected that directories should be empty.
- If a directory is not empty, do not remove the directory.
    - Issue a warning to the user and continue on.
- Before removing directories, verify that no DataGroup is still installed.
    - If installed DataGroup files are still present, the script must exit with non-zero status and print a clear error message instructing the user to uninstall DataGroups first.
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

*Step*: Validate requested DataGroup
- If `<dataGroup>` is not listed in `dataGroupList`, the script must exit with non-zero status and print a clear error message identifying the unsupported dataGroup.
- If another DataGroup is already installed, the script must continue and install the requested DataGroup alongside it, provided the target file paths do not conflict.

*Step*: Determine the destination as specified in [Core Concept](#the-core-concept)
- If a file's Tag cannot be resolved to exactly one destination directory in FrameData, the script must exit with non-zero status and print a clear error message identifying the file and Tag.
- If the resolved destination directory does not exist, the script must exit with non-zero status and print a clear error message instructing the user to install the Frame first.

*Step*: Copy files to the target directories as specified by:
- [Data Group Config File](#data-group-config-file-definitions) and 
- [Frame Data Config File Definition](#frame-data-config-file-definition)
- If the source file listed in the DataGroup config is missing at install time, the script must exit with non-zero status and print a clear error message identifying the missing source file.
- If the destination path exists as a directory when a file write is required, the script must exit with non-zero status and print a clear error message identifying the conflicting path.
- If a file copy or overwrite fails because of permissions or another OS error, the script must exit with non-zero status and print a clear error message identifying the source and destination paths involved.


### Uninstall DataGroup
----------------------------------------------------------------------------------------------------

This behavior is initiated by [CLI Uninstall DataGroup](#uninstall-datagroup)

*Step*: Read frameData.config.json
- Verify the file is correct. 

*Step*: Read <dataGroup>.dataGroup.json
- Verify the file is correct.

*Step*: Validate requested DataGroup
- If `<dataGroup>` is not listed in `dataGroupList`, the script must exit with non-zero status and print a clear error message identifying the unsupported dataGroup.
- If the requested DataGroup is not currently installed, the script must warn the user and make no filesystem changes.

*Step*: Determine the location of the files to be removed as specified in [Core Concept](#the-core-concept)
- If a file's Tag cannot be resolved to exactly one destination directory in FrameData, the script must exit with non-zero status and print a clear error message identifying the file and Tag.

*Step*: Remove the specified files from the Framework.
- Situations that may be encountered
    - File is present
        - Normal case
        - Remove file
    - File is not present
        - Exception case
        - Warn the user that the file to be removed is missing.
    - The resolved path exists as a directory instead of a file
        - Exception case
        - Warn the user and skip removal for that entry.
    - The process does not have permission to remove the file
        - Exception case
        - Exit with non-zero status and print a clear error message identifying the file path that could not be removed.



## Error Messages
- sys.exit(1) with an error message if the validation fails