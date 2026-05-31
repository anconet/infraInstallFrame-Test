#!/usr/bin/env python3

"""Install and uninstall frame directories and datagroups.

This script implements the behavior described in frame.spec.md.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Literal, TypedDict, cast

Kind = Literal["location", "file"]
WritePolicy = Literal["force", "copy", "skip"]

FRAME_CONFIG_NAME = "frameData.config.json"
RESERVED_FILE_CHARS = set('<>:"|?*')
RESERVED_WINDOWS_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}


class Tag(TypedDict):
    """Tag that maps datagroup files to a destination directory."""

    kind: Kind
    name: str

    @staticmethod
    def validate(obj: dict[str, Any]) -> Tag:
        """Validate a raw JSON object as a Tag."""
        if "kind" not in obj or not isinstance(obj["kind"], str):
            raise ValueError("Invalid Tag: 'kind' is required and must be a string")
        if obj["kind"] not in {"location", "file"}:
            raise ValueError("Invalid Tag: 'kind' must be 'location' or 'file'")
        if "name" not in obj or not isinstance(obj["name"], str):
            raise ValueError("Invalid Tag: 'name' is required and must be a string")
        if obj["name"] == "":
            raise ValueError("Invalid Tag: 'name' must be non-empty")
        if not obj["name"].replace("_", "").isalnum():
            raise ValueError(
                "Invalid Tag: 'name' must contain only alphanumeric characters and underscores"
            )
        return cast(Tag, obj)


class FileEntry(TypedDict):
    """Single source file declaration for a datagroup."""

    name: str
    tag: Tag
    writePolicy: WritePolicy

    @staticmethod
    def validate(obj: dict[str, Any]) -> FileEntry:
        """Validate a raw JSON object as a datagroup file entry."""
        if "name" not in obj or not isinstance(obj["name"], str):
            raise ValueError("Invalid File: 'name' is required and must be a string")
        fileName = obj["name"]
        if fileName == "":
            raise ValueError("Invalid File: 'name' must be non-empty")
        if "/" in fileName or "\\" in fileName:
            raise ValueError("Invalid File: 'name' must not include path separators")
        for reservedChar in RESERVED_FILE_CHARS:
            if reservedChar in fileName:
                raise ValueError(
                    f"Invalid File: 'name' contains reserved character '{reservedChar}'"
                )
        fileStem = fileName.split(".", 1)[0].upper()
        if fileStem in RESERVED_WINDOWS_NAMES:
            raise ValueError(f"Invalid File: 'name' uses reserved name '{fileStem}'")

        if "tag" not in obj or not isinstance(obj["tag"], dict):
            raise ValueError("Invalid File: 'tag' is required and must be an object")
        tagObj = Tag.validate(cast(dict[str, Any], obj["tag"]))
        obj["tag"] = tagObj

        if "writePolicy" not in obj or not isinstance(obj["writePolicy"], str):
            raise ValueError(
                "Invalid File: 'writePolicy' is required and must be a string"
            )
        if obj["writePolicy"] not in {"force", "copy", "skip"}:
            raise ValueError(
                "Invalid File: 'writePolicy' must be 'force', 'copy', or 'skip'"
            )

        return cast(FileEntry, obj)


class DataGroup(TypedDict):
    """Datagroup configuration containing files to install."""

    fileList: list[FileEntry]

    @staticmethod
    def validate(obj: dict[str, Any]) -> DataGroup:
        """Validate a raw JSON object as a DataGroup."""
        if "fileList" not in obj:
            raise ValueError("Invalid DataGroup: missing required key 'fileList'")
        if not isinstance(obj["fileList"], list):
            raise ValueError("Invalid DataGroup: 'fileList' must be an array")

        rawFileList = cast(list[Any], obj["fileList"])
        if len(rawFileList) == 0:
            raise ValueError("Invalid DataGroup: 'fileList' must contain at least one entry")

        seenFileNames: set[str] = set()
        validatedFileList: list[FileEntry] = []
        for fileObj in rawFileList:
            if not isinstance(fileObj, dict):
                raise ValueError("Invalid DataGroup: each fileList entry must be an object")
            validatedFile = FileEntry.validate(cast(dict[str, Any], fileObj))
            fileName = validatedFile["name"]
            if fileName in seenFileNames:
                raise ValueError(f"Invalid DataGroup: duplicate file entry '{fileName}'")
            seenFileNames.add(fileName)
            validatedFileList.append(validatedFile)

        obj["fileList"] = validatedFileList
        return cast(DataGroup, obj)


class Directory(TypedDict):
    """Directory node in the frame directory tree."""

    name: str
    tagList: list[Tag]
    directoryList: list["Directory"]

    @staticmethod
    def validate(obj: dict[str, Any]) -> Directory:
        """Validate directory structure shape and nested objects."""
        if "name" not in obj or not isinstance(obj["name"], str):
            raise ValueError("Invalid Directory: 'name' is required and must be a string")
        if obj["name"] == "":
            raise ValueError("Invalid Directory: 'name' must be non-empty")
        if "/" in obj["name"] or "\\" in obj["name"]:
            raise ValueError("Invalid Directory: 'name' must not include path separators")
        for reservedChar in RESERVED_FILE_CHARS:
            if reservedChar in obj["name"]:
                raise ValueError(
                    f"Invalid Directory: 'name' contains reserved character '{reservedChar}'"
                )

        if "tagList" not in obj or not isinstance(obj["tagList"], list):
            raise ValueError("Invalid Directory: 'tagList' is required and must be an array")
        if "directoryList" not in obj or not isinstance(obj["directoryList"], list):
            raise ValueError(
                "Invalid Directory: 'directoryList' is required and must be an array"
            )

        validatedTagList: list[Tag] = []
        for rawTag in cast(list[Any], obj["tagList"]):
            if not isinstance(rawTag, dict):
                raise ValueError("Invalid Directory: each tagList entry must be an object")
            validatedTag = Tag.validate(cast(dict[str, Any], rawTag))
            validatedTagList.append(validatedTag)

        validatedDirectoryList: list[Directory] = []
        seenChildNames: set[str] = set()
        for rawDirectory in cast(list[Any], obj["directoryList"]):
            if not isinstance(rawDirectory, dict):
                raise ValueError(
                    "Invalid Directory: each directoryList entry must be an object"
                )
            validatedDirectory = Directory.validate(cast(dict[str, Any], rawDirectory))
            childName = validatedDirectory["name"]
            if childName in seenChildNames:
                raise ValueError(
                    f"Invalid Directory: duplicate child directory name '{childName}'"
                )
            seenChildNames.add(childName)
            validatedDirectoryList.append(validatedDirectory)

        obj["tagList"] = validatedTagList
        obj["directoryList"] = validatedDirectoryList
        return cast(Directory, obj)


class FrameData(TypedDict):
    """Frame installation configuration loaded from frameData.config.json."""

    projectDirectory: str
    tagList: list[Tag]
    directoryList: list[Directory]
    dataGroupList: list[str]

    @staticmethod
    def validate(obj: dict[str, Any]) -> FrameData:
        """Validate top-level frame config structure and basic types."""
        requiredKeys = ["projectDirectory", "tagList", "directoryList", "dataGroupList"]
        for requiredKey in requiredKeys:
            if requiredKey not in obj:
                raise ValueError(
                    f"Invalid FrameData: missing required top-level key '{requiredKey}'"
                )

        if not isinstance(obj["projectDirectory"], str):
            raise ValueError("Invalid FrameData: 'projectDirectory' must be a string")
        if not isinstance(obj["tagList"], list):
            raise ValueError("Invalid FrameData: 'tagList' must be an array")
        if not isinstance(obj["directoryList"], list):
            raise ValueError("Invalid FrameData: 'directoryList' must be an array")
        if not isinstance(obj["dataGroupList"], list):
            raise ValueError("Invalid FrameData: 'dataGroupList' must be an array")

        validatedTagList: list[Tag] = []
        for rawTag in cast(list[Any], obj["tagList"]):
            if not isinstance(rawTag, dict):
                raise ValueError("Invalid FrameData: each tagList entry must be an object")
            validatedTag = Tag.validate(cast(dict[str, Any], rawTag))
            validatedTagList.append(validatedTag)

        validatedDirectoryList: list[Directory] = []
        seenTopDirectoryNames: set[str] = set()
        for rawDirectory in cast(list[Any], obj["directoryList"]):
            if not isinstance(rawDirectory, dict):
                raise ValueError(
                    "Invalid FrameData: each directoryList entry must be an object"
                )
            validatedDirectory = Directory.validate(cast(dict[str, Any], rawDirectory))
            directoryName = validatedDirectory["name"]
            if directoryName in seenTopDirectoryNames:
                raise ValueError(
                    f"Invalid FrameData: duplicate top-level directory '{directoryName}'"
                )
            seenTopDirectoryNames.add(directoryName)
            validatedDirectoryList.append(validatedDirectory)

        validatedDataGroupList: list[str] = []
        seenDataGroupNames: set[str] = set()
        for rawDataGroup in cast(list[Any], obj["dataGroupList"]):
            if not isinstance(rawDataGroup, str):
                raise ValueError("Invalid FrameData: dataGroupList must contain only strings")
            if rawDataGroup in seenDataGroupNames:
                raise ValueError(
                    f"Invalid FrameData: duplicate dataGroup entry '{rawDataGroup}'"
                )
            seenDataGroupNames.add(rawDataGroup)
            validatedDataGroupList.append(rawDataGroup)

        obj["tagList"] = validatedTagList
        obj["directoryList"] = validatedDirectoryList
        obj["dataGroupList"] = validatedDataGroupList
        return cast(FrameData, obj)


class PathContext(TypedDict):
    """Resolved paths for Project repo and Parent target roots."""

    projectRoot: Path
    targetRoot: Path


def fail(message: str) -> None:
    """Print an error message and exit with status code 1."""
    print(f"Error: {message}")
    sys.exit(1)


def warn(message: str) -> None:
    """Print a warning message."""
    print(f"Warning: {message}")


def loadJsonFile(filePath: Path) -> dict[str, Any]:
    """Load a JSON file and return the object with user-facing errors."""
    if not filePath.exists():
        fail(f"{filePath} not found")
    try:
        with filePath.open("r", encoding="utf-8") as inputFile:
            loaded = json.load(inputFile)
    except JSONDecodeError as error:
        fail(f"Failed to parse JSON in {filePath}: {error}")
    except OSError as error:
        fail(f"Unable to read {filePath}: {error}")

    if not isinstance(loaded, dict):
        fail(f"{filePath} must contain a top-level JSON object")
    return cast(dict[str, Any], loaded)


def writeJsonFile(filePath: Path, payload: dict[str, Any]) -> None:
    """Write JSON to disk with stable formatting."""
    try:
        with filePath.open("w", encoding="utf-8") as outputFile:
            json.dump(payload, outputFile, indent=2)
    except OSError as error:
        fail(f"Unable to write {filePath}: {error}")


def resolveTargetRoot(projectRoot: Path, frameData: FrameData) -> Path:
    """Resolve and validate the install target root in the Parent repo."""
    projectDirectory = frameData["projectDirectory"]
    projectDirectoryPath = Path(projectDirectory)

    if projectDirectoryPath.is_absolute():
        fail("FrameData projectDirectory must be relative and cannot be absolute")

    for pathPart in projectDirectoryPath.parts:
        if pathPart == "..":
            fail("FrameData projectDirectory must not contain path traversal '..'")

    resolvedTargetRoot = projectRoot.parent.joinpath(projectDirectoryPath)
    if not resolvedTargetRoot.exists():
        fail(
            f"Resolved projectDirectory does not exist: {resolvedTargetRoot}"
        )

    return resolvedTargetRoot


def flattenDirectories(
    parentPath: Path,
    directoryList: list[Directory],
) -> list[Path]:
    """Flatten nested directory definitions into absolute directory paths."""
    flattened: list[Path] = []
    seenResolvedPaths: set[Path] = set()

    def walkDirectories(currentParent: Path, currentDirectories: list[Directory]) -> None:
        """Recursively accumulate resolved directory paths."""
        for directoryObj in currentDirectories:
            resolvedPath = currentParent.joinpath(directoryObj["name"])
            if resolvedPath in seenResolvedPaths:
                fail(f"Conflicting directory definitions resolve to {resolvedPath}")
            seenResolvedPaths.add(resolvedPath)
            flattened.append(resolvedPath)
            walkDirectories(resolvedPath, directoryObj["directoryList"])

    walkDirectories(parentPath, directoryList)
    return flattened


def buildTagDestinationMap(
    parentPath: Path,
    frameData: FrameData,
) -> dict[tuple[str, str], list[Path]]:
    """Build map from tag key to one or more destination directories."""
    tagDestinationMap: dict[tuple[str, str], list[Path]] = {}

    def addTagDestination(tagObj: Tag, destinationPath: Path) -> None:
        """Append a destination path for a specific tag key."""
        tagKey = (tagObj["kind"], tagObj["name"])
        if tagKey not in tagDestinationMap:
            tagDestinationMap[tagKey] = []
        tagDestinationMap[tagKey].append(destinationPath)

    for rootTag in frameData["tagList"]:
        addTagDestination(rootTag, parentPath)

    def walkDirectories(currentParent: Path, currentDirectories: list[Directory]) -> None:
        """Walk directories and register tag destinations."""
        for directoryObj in currentDirectories:
            directoryPath = currentParent.joinpath(directoryObj["name"])
            for tagObj in directoryObj["tagList"]:
                addTagDestination(tagObj, directoryPath)
            walkDirectories(directoryPath, directoryObj["directoryList"])

    walkDirectories(parentPath, frameData["directoryList"])
    return tagDestinationMap


def validateTagUniqueness(frameData: FrameData) -> None:
    """Ensure every Tag.name is unique across the project config."""
    seenTagNames: set[str] = set()

    def registerTag(tagObj: Tag) -> None:
        """Register one tag name and enforce global uniqueness."""
        tagName = tagObj["name"]
        if tagName in seenTagNames:
            fail(f"Duplicate Tag.name detected in frame config: '{tagName}'")
        seenTagNames.add(tagName)

    for rootTag in frameData["tagList"]:
        registerTag(rootTag)

    def walkDirectories(currentDirectories: list[Directory]) -> None:
        """Recursively register tags from directory tree."""
        for directoryObj in currentDirectories:
            for tagObj in directoryObj["tagList"]:
                registerTag(tagObj)
            walkDirectories(directoryObj["directoryList"])

    walkDirectories(frameData["directoryList"])


def resolveGroupDirectory(projectRoot: Path, dataGroupName: str) -> Path:
    """Return the datagroup directory path, validating existence."""
    groupDirectory = projectRoot.joinpath(dataGroupName)
    if not groupDirectory.exists() or not groupDirectory.is_dir():
        fail(f"DataGroup directory not found: {groupDirectory}")
    return groupDirectory


def resolveGroupConfigPath(groupDirectory: Path, dataGroupName: str) -> Path:
    """Return datagroup config path, validating file presence."""
    groupConfigPath = groupDirectory.joinpath(f"{dataGroupName}.dataGroup.json")
    if not groupConfigPath.exists():
        fail(f"DataGroup config file not found: {groupConfigPath}")
    return groupConfigPath


def loadAndValidateFrameData(projectRoot: Path) -> tuple[FrameData, PathContext]:
    """Load, validate, and normalize frame configuration and path context."""
    frameConfigPath = projectRoot.joinpath(FRAME_CONFIG_NAME)
    rawFrameDataObj = loadJsonFile(frameConfigPath)
    try:
        frameData = FrameData.validate(rawFrameDataObj)
    except ValueError as error:
        fail(str(error))

    validateTagUniqueness(frameData)

    targetRoot = resolveTargetRoot(projectRoot, frameData)

    for dataGroupName in frameData["dataGroupList"]:
        groupDirectory = projectRoot.joinpath(dataGroupName)
        if not groupDirectory.exists() or not groupDirectory.is_dir():
            fail(
                "DataGroup listed in frameData is missing directory: "
                f"{groupDirectory}"
            )
        groupConfigPath = groupDirectory.joinpath(f"{dataGroupName}.dataGroup.json")
        if not groupConfigPath.exists() or not groupConfigPath.is_file():
            fail(
                "DataGroup listed in frameData is missing config file: "
                f"{groupConfigPath}"
            )

    pathContext: PathContext = PathContext(
        projectRoot=projectRoot,
        targetRoot=targetRoot,
    )
    return frameData, pathContext


def loadAndValidateDataGroup(projectRoot: Path, dataGroupName: str) -> tuple[DataGroup, Path]:
    """Load and validate one datagroup file and source file existence."""
    groupDirectory = resolveGroupDirectory(projectRoot, dataGroupName)
    groupConfigPath = resolveGroupConfigPath(groupDirectory, dataGroupName)
    rawDataGroupObj = loadJsonFile(groupConfigPath)

    try:
        dataGroup = DataGroup.validate(rawDataGroupObj)
    except ValueError as error:
        fail(str(error))

    for fileEntry in dataGroup["fileList"]:
        sourcePath = groupDirectory.joinpath(fileEntry["name"])
        if not sourcePath.exists() or not sourcePath.is_file():
            fail(f"Source file listed in DataGroup is missing: {sourcePath}")

    return dataGroup, groupDirectory


def resolveDestinationDirectory(
    fileEntry: FileEntry,
    tagDestinationMap: dict[tuple[str, str], list[Path]],
) -> Path:
    """Resolve a file entry tag to exactly one destination directory."""
    tagObj = fileEntry["tag"]
    tagKey = (tagObj["kind"], tagObj["name"])
    destinationList = tagDestinationMap.get(tagKey, [])
    if len(destinationList) != 1:
        fail(
            "Unable to resolve tag to exactly one destination for file "
            f"'{fileEntry['name']}', tag={tagObj}"
        )
    return destinationList[0]


def installFrame(frameData: FrameData, targetRoot: Path) -> None:
    """Create the directory tree defined by frameData."""
    allDirectories = flattenDirectories(targetRoot, frameData["directoryList"])

    for directoryPath in allDirectories:
        if directoryPath.exists() and directoryPath.is_file():
            fail(f"Cannot create directory because a file exists at: {directoryPath}")
        if directoryPath.exists() and directoryPath.is_dir():
            warn(f"Directory already exists, skipping: {directoryPath}")
            continue
        try:
            directoryPath.mkdir(parents=True, exist_ok=False)
        except PermissionError:
            fail(f"Permission denied creating directory: {directoryPath}")
        except OSError as error:
            fail(f"Failed to create directory {directoryPath}: {error}")


def detectInstalledDataGroups(
    frameData: FrameData,
    projectRoot: Path,
    targetRoot: Path,
) -> list[str]:
    """Detect datagroups with at least one file currently present in destinations."""
    installedDataGroups: list[str] = []
    tagDestinationMap = buildTagDestinationMap(targetRoot, frameData)

    for dataGroupName in frameData["dataGroupList"]:
        groupDirectory = projectRoot.joinpath(dataGroupName)
        groupConfigPath = groupDirectory.joinpath(f"{dataGroupName}.dataGroup.json")
        if not groupConfigPath.exists():
            continue
        rawDataGroupObj = loadJsonFile(groupConfigPath)
        try:
            dataGroup = DataGroup.validate(rawDataGroupObj)
        except ValueError:
            continue

        isInstalled = False
        for fileEntry in dataGroup["fileList"]:
            destinationDirectory = resolveDestinationDirectory(fileEntry, tagDestinationMap)
            destinationPath = destinationDirectory.joinpath(fileEntry["name"])
            if destinationPath.exists():
                isInstalled = True
                break
        if isInstalled:
            installedDataGroups.append(dataGroupName)

    return installedDataGroups


def uninstallFrame(frameData: FrameData, pathContext: PathContext) -> None:
    """Attempt to remove frame directories, leaving non-empty directories intact."""
    projectRoot = pathContext["projectRoot"]
    targetRoot = pathContext["targetRoot"]

    detectedInstalled = detectInstalledDataGroups(frameData, projectRoot, targetRoot)
    if len(detectedInstalled) > 0:
        fail(
            "DataGroup files are still present. Uninstall DataGroups first: "
            f"{', '.join(detectedInstalled)}"
        )

    allDirectories = flattenDirectories(targetRoot, frameData["directoryList"])
    allDirectories.sort(key=lambda pathObj: len(pathObj.parts), reverse=True)

    for directoryPath in allDirectories:
        if not directoryPath.exists():
            warn(f"Directory does not exist during uninstall, skipping: {directoryPath}")
            continue
        if directoryPath.is_file():
            warn(f"Expected a directory but found a file, skipping: {directoryPath}")
            continue

        try:
            if any(directoryPath.iterdir()):
                warn(f"Directory is not empty, skipping removal: {directoryPath}")
                continue
            directoryPath.rmdir()
        except PermissionError:
            fail(f"Permission denied removing directory: {directoryPath}")
        except OSError as error:
            fail(f"Failed removing directory {directoryPath}: {error}")


def ensureSupportedDataGroup(frameData: FrameData, dataGroupName: str) -> None:
    """Ensure requested datagroup exists in frameData dataGroupList."""
    if dataGroupName not in frameData["dataGroupList"]:
        fail(f"Unsupported DataGroup requested: {dataGroupName}")


def applyWritePolicy(
    sourcePath: Path,
    destinationPath: Path,
    writePolicy: WritePolicy,
) -> None:
    """Apply write policy for one source and destination file pair."""
    if destinationPath.exists() and destinationPath.is_dir():
        fail(
            "Destination path exists as a directory where a file is required: "
            f"{destinationPath}"
        )

    if writePolicy == "force":
        try:
            shutil.copy2(sourcePath, destinationPath)
        except OSError as error:
            fail(f"Failed copying {sourcePath} -> {destinationPath}: {error}")
        return

    if writePolicy == "copy":
        if destinationPath.exists():
            tmpDestinationPath = destinationPath.with_name(
                f"{destinationPath.stem}.tmp"
            )
            suffixCounter = 1
            while tmpDestinationPath.exists():
                tmpDestinationPath = destinationPath.with_name(
                    f"{destinationPath.stem}-{suffixCounter}.tmp"
                )
                suffixCounter += 1
            try:
                shutil.copy2(sourcePath, tmpDestinationPath)
            except OSError as error:
                fail(f"Failed copying {sourcePath} -> {tmpDestinationPath}: {error}")
        else:
            try:
                shutil.copy2(sourcePath, destinationPath)
            except OSError as error:
                fail(f"Failed copying {sourcePath} -> {destinationPath}: {error}")
        return

    if writePolicy == "skip":
        if destinationPath.exists():
            return
        try:
            shutil.copy2(sourcePath, destinationPath)
        except OSError as error:
            fail(f"Failed copying {sourcePath} -> {destinationPath}: {error}")
        return

    fail(f"Unknown write policy '{writePolicy}'")


def installDataGroup(frameData: FrameData, pathContext: PathContext, dataGroupName: str) -> None:
    """Install one datagroup into resolved frame directories."""
    projectRoot = pathContext["projectRoot"]
    targetRoot = pathContext["targetRoot"]

    ensureSupportedDataGroup(frameData, dataGroupName)

    dataGroup, groupDirectory = loadAndValidateDataGroup(projectRoot, dataGroupName)
    tagDestinationMap = buildTagDestinationMap(targetRoot, frameData)

    for fileEntry in dataGroup["fileList"]:
        destinationDirectory = resolveDestinationDirectory(fileEntry, tagDestinationMap)
        if not destinationDirectory.exists() or not destinationDirectory.is_dir():
            fail(
                "Resolved destination directory does not exist. Install frame first: "
                f"{destinationDirectory}"
            )

        sourcePath = groupDirectory.joinpath(fileEntry["name"])
        destinationPath = destinationDirectory.joinpath(fileEntry["name"])
        applyWritePolicy(sourcePath, destinationPath, fileEntry["writePolicy"])


def uninstallDataGroup(
    frameData: FrameData,
    pathContext: PathContext,
    dataGroupName: str,
) -> None:
    """Uninstall one datagroup from resolved frame directories."""
    projectRoot = pathContext["projectRoot"]
    targetRoot = pathContext["targetRoot"]

    ensureSupportedDataGroup(frameData, dataGroupName)

    dataGroup, _groupDirectory = loadAndValidateDataGroup(projectRoot, dataGroupName)
    tagDestinationMap = buildTagDestinationMap(targetRoot, frameData)

    isInstalled = False
    for fileEntry in dataGroup["fileList"]:
        destinationDirectory = resolveDestinationDirectory(fileEntry, tagDestinationMap)
        destinationPath = destinationDirectory.joinpath(fileEntry["name"])
        if destinationPath.exists():
            isInstalled = True
            break

    if not isInstalled:
        warn(
            "Requested DataGroup is not currently installed; no filesystem changes made"
        )
        return

    for fileEntry in dataGroup["fileList"]:
        destinationDirectory = resolveDestinationDirectory(fileEntry, tagDestinationMap)
        destinationPath = destinationDirectory.joinpath(fileEntry["name"])

        if not destinationPath.exists():
            warn(f"File to uninstall is missing: {destinationPath}")
            continue

        if destinationPath.is_dir():
            warn(
                "Resolved uninstall path is a directory, skipping file removal: "
                f"{destinationPath}"
            )
            continue

        try:
            destinationPath.unlink()
        except PermissionError:
            fail(f"Permission denied removing file: {destinationPath}")
        except OSError as error:
            fail(f"Failed removing file {destinationPath}: {error}")


def parseArgs() -> argparse.Namespace:
    """Parse CLI arguments for frame and datagroup operations."""
    parser = argparse.ArgumentParser(
        description="Install or uninstall frame directories and datagroup files"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    frameParser = subparsers.add_parser("frame", help="Install or uninstall frame")
    frameParser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall frame directory structure",
    )

    dataGroupParser = subparsers.add_parser(
        "datagroup", help="Install or uninstall a datagroup"
    )
    dataGroupParser.add_argument(
        "--uninstall",
        action="store_true",
        help="Uninstall datagroup files",
    )
    dataGroupParser.add_argument("dataGroupName", help="DataGroup name")

    return parser.parse_args()


def main() -> None:
    """Run the installer CLI."""
    args = parseArgs()

    projectRoot = Path(os.getcwd())
    frameData, pathContext = loadAndValidateFrameData(projectRoot)

    if args.command == "frame":
        if args.uninstall:
            uninstallFrame(frameData, pathContext)
        else:
            installFrame(frameData, pathContext["targetRoot"])
        return

    if args.command == "datagroup":
        dataGroupName = cast(str, args.dataGroupName)
        if args.uninstall:
            uninstallDataGroup(frameData, pathContext, dataGroupName)
        else:
            installDataGroup(frameData, pathContext, dataGroupName)
        return

    fail(f"Unsupported command: {args.command}")


if __name__ == "__main__":
    main()
