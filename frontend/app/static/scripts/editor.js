const allTags = new Set();
document.querySelectorAll("[data-tag]").forEach(tagBtn => {
    allTags.add(tagBtn.getAttribute("data-tag"));
});
const allTypes = new Set();
document.querySelectorAll("[data-type]").forEach(typeBtn => {
    allTypes.add(typeBtn.getAttribute("data-type"));
});

const selectedTags = new Set();
const selectedTypes = new Set(allTypes);
// const missingTags = new Set();
// document.querySelectorAll('.tag-btn').forEach(tagButton => {
//     missingTags.add(tagButton.dataset.id);
// });
let allTagsSelected = false;
let allTypesSelected = true;

function toggleTagSelection(tag) {
    let tagButton = document.getElementById(`tagBtn-${tag}`);
    tagButton.classList.toggle("active");
    if (selectedTags.has(tag)) {
        selectedTags.delete(tag);
    } else {
        selectedTags.add(tag);
    }
    console.log(selectedTags);
    allTagsSelected = (selectedTags.size == allTags.size);
    console.log(allTagsSelected);
    console.log(allTags);
}

function toggleTypeSelection(type) {
    let typeButton = document.getElementById(`typeBtn-${type}`);
    typeButton.classList.toggle("active");
    if (selectedTypes.has(type)) {
        selectedTypes.delete(type);
    } else {
        selectedTypes.add(type);
    }
    console.log(selectedTypes);
    allTypesSelected = (selectedTypes.size == allTypes.size);
    console.log(allTypesSelected);
    console.log(allTypes);
}

function toggleAllTags() {
    allTags.forEach(tag => {
        toggleTagSelection(tag);
    });
}

function toggleAllTypes() {
    allTypes.forEach(type => {
        toggleTypeSelection(type);
    });
}

function createTag() {
    let tagInput = document.getElementById("newTag").value;
    if (String.prototype.trim.call(tagInput) === "") {
        return;
    }
    let tagObject = {name: tagInput};
    fetch('/forward/create_tag/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(tagObject)
    })
        .then(resp => {
            if (resp.ok) {
                location.reload();
            }
        });
}

// function onTagSelect(tagName, button) {
//     console.log(tagName + " selected");
//     if (tagName == "@allTags") {
//         if (allSelected) {
//             selectedTags.clear();
//             document.querySelectorAll('#tagSelector>.tag-btn').forEach(tagButton => {
//                 missingTags.add(tagButton.dataset.id);
//             });
//         } else {
//             document.querySelectorAll('#tagSelector>.tag-btn').forEach(tagButton => {
//                 selectedTags.add(tagButton.dataset.id);
//             });
//             missingTags.clear();
//         }
//         allSelected = !allSelected;
//     } else {
//         if (selectedTags.has(tagName)) {
//             selectedTags.delete(tagName);
//             missingTags.add(tagName);
//             selectedTags.delete('@allTags');
//             missingTags.add('@allTags');
//             allSelected = true;
//         } else {
//             selectedTags.add(tagName);
//             missingTags.delete(tagName);
//         }
//     }
//     if (missingTags.size == 1 && missingTags.has('@allTags')) {
//         selectedTags.add('@allTags');
//         missingTags.delete('@allTags');
//         allSelected = true;
//     }
//     document.querySelectorAll('.tag-btn').forEach(tagButton => {
//         if (selectedTags.has(tagButton.dataset.id)) {
//             tagButton.classList.add('active');
//         } else {
//             tagButton.classList.remove('active');
//         }
//     });
//     console.log(missingTags);
//     console.log(selectedTags);
// };

// document.querySelectorAll('.tag-btn').forEach(button => {
//     button.addEventListener('click', event => {
//         onTagSelect(button.dataset.id, button);
//     });
// });

let graphContainer = document.getElementById('graph');

let network_data = {
    nodes: nodes,
    edges: edges
};

const NETWORK_OPTIONS = {
    layout: {
        randomSeed: 466,
        improvedLayout: true,
        hierarchical: {
            enabled: true,
            levelSeparation: 150,
            nodeSpacing: 100,
            treeSpacing: 200,
            blockShifting: true,
            edgeMinimization: true,
            parentCentralization: true,
            direction: 'DU',        // UD, DU, LR, RL
            sortMethod: 'hubsize'   // hubsize, directed
        }
    },
    edges: {
        arrows: {
            to: {
                enabled: true,
                scaleFactor: 0.5,
                type: "arrow"
            },
            from: {
                enabled: false,
                scaleFactor: 1,
                type: "arrow"
            }
        },
        font: {
            strokeWidth: 0, // px
            color: '#fafafa',
            multi: 'md'
        }
    },
    nodes: {
        font: {
            strokeWidth: 0, // px
            color: '#fafafa',
            multi: 'md'
        },
        color: {
            border: '#848484',
            background: '#84848488',
            highlight: {
                border: '#fafafa88',
                background: '#848484'
            }
        },
        chosen: true,
    }
};

let network = new vis.Network(graphContainer, network_data, NETWORK_OPTIONS);
// network.setOptions(NETWORK_OPTIONS);
console.log(network_data);

function getActualSelectedElement() {
    selection = network.getSelection();
    console.log(selection);
    if (!selection) {
        return;
    }
    let selectedAsset = null;

    if (selection['nodes'].length > 0) {
        nodeOrEdge = 'nodes';
        selectedAsset = selection['nodes'][0];
    } else {
        nodeOrEdge = 'edges';
        selectedAsset = selection['edges'][0];
    }
    selectionType = selectedAsset.split('/')[0];
    selectionKey = selectedAsset.split('/')[1];
    return selectedAsset;
}

let editor;
let notesEditor;

let selection;
let nodeOrEdge;
let selectionType;
let selectionKey;

network.on('deselectNode', event => {
    resetEditor();
});

network.on('deselectEdge', event => {
    resetEditor();
});

network.on('selectEdge', event => {
    console.log("edge selected");
    selection = getActualSelectedElement();
    if (nodeOrEdge == 'nodes') {
        return;
    }
    refreshEditor(selection);
});

network.on('selectNode', event => {
    console.log("node selected");
    selection = getActualSelectedElement();
    if (!selection) {
        resetEditor(); return;
    }
    refreshEditor(selection);
});

const assetSavedHtml = `<i class="bi bi-check me-2"></i>Saved!`;
const assetNotSavedHtml = `<i class="bi bi-floppy me-2"></i>Save`;
const assetSaveFailedHtml = `<i class="bi bi-x me-2"></i>Failed to save`;

const replaceMap = {
    "_id": "db_id",
    "_key": "db_key"
};

function saveAsset() {
    let asset = editor.getValue();
    delete asset.id;
    delete asset.label;
    for (let key in replaceMap) {
        if (replaceMap.hasOwnProperty(key) && asset.hasOwnProperty(key)) {
            asset[replaceMap[key]] = asset[key];
            delete asset[key];
        }
    }
    console.log(asset);
    saveBtn = document.getElementById("save-btn");
    fetch('/forward/update_asset/' + selectionType, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(asset)
    })
        .then(resp => {
            if (resp.status !== 200) {
                saveBtn.innerHTML = assetSaveFailedHtml;
                saveBtn.classList.toggle('btn-danger');
                saveBtn.classList.toggle('btn-success');
            } else {
                saveBtn.innerHTML = assetSavedHtml;
            }
            setTimeout(() => {
                saveBtn.classList.remove('btn-danger');
                saveBtn.classList.add('btn-success');
                saveBtn.innerHTML = assetNotSavedHtml;
            }, 2000);
            return resp.text();
        });
}

const notesSavedHtml = `<i class="bi bi-check me-2"></i>Notes saved!`;
const notesNotSavedHtml = `<i class="bi bi-journal me-2"></i>Save notes`;

function saveNotes() {
    let notes = notesEditor.getValue();
    fetch('/forward/set_notes/' + selectionType + "/" + selectionKey, {
        method: 'POST',
        body: notes
    }).then(resp => { console.log(resp); resp.text(); });
    saveBtn = document.getElementById("save-notes-btn");
    saveBtn.innerHTML = notesSavedHtml;
    setTimeout(() => {
        saveBtn.innerHTML = notesNotSavedHtml;
    }, 2000);
}

function deleteAsset() {
    fetch('/forward/delete_asset/' + selectionType + "/" + selectionKey, {
        method: 'POST'
    }).then(resp => { console.log(resp); resp.text(); });
    setTimeout(() => {
        location.reload();
    }, 1000);
}

function resetEditor() {
    document.getElementById("data-type-text").innerHTML = "Asset Editor";
    document.getElementById("json-editor-container").innerHTML = "";
    document.getElementById("notes-container").innerHTML = "";
    // document.getElementById("save-btn").hidden = true;
    // document.getElementById("delete-btn").hidden = true;
    document.getElementById("editorControls").hidden = true;
    document.getElementById("editorTagContainer").hidden = true;
}

const hiddenEditors = ['root.id', 'root._id', 'root.type', 'root.label', 'root.from', 'root.to'];
const disabledEditors = ['root._key', 'root._from', 'root._to'];


function toggleTagOnNode(tag) {
    fetch(`/forward/toggle_tag/${selectionType}/${selectionKey}/${tag}`, {
        method: 'POST'
    })
    .then(resp => {
        if (resp.ok) {
            let tagButton = document.getElementById(`nodeTagBtn-${tag}`);
            tagButton.classList.toggle("active");
        }
    });
    // .then(resp => resp.text());
}


async function refreshEditor(networkElement) {
    if (editor) {
        editor.destroy();
    }
    if (notesEditor) {
        notesEditor.destroy();
    }
    document.getElementById("editorControls").hidden = false;
    console.log(networkElement);
    document.getElementById("data-type-text").innerHTML = "" + networkElement;
    let editorContainer = document.getElementById("json-editor-container");
    editorContainer.innerHTML = "";
    // if (editor) {
    //     editor.destroy();
    // }

    let schema;
    await fetch(`/forward/get_model/${selectionType}`).then(response => response.json()).then(data => {
        schema = data["model_schema"];
        console.log(schema);
    });

    let asset = await fetch(`/forward/get_asset/${selectionType}/${selectionKey}`).then(response => response.json());

    let assetTags = await fetch(`/forward/get_tags/${selectionType}/${selectionKey}`).then(response => response.json());
    console.log("tags:" + assetTags);
    let tagContainer = document.getElementById("nodeTagContainer");
    tagContainer.innerHTML = "";
    let inactiveTags = new Set(allTags);
    assetTags.forEach(tag => {
        // <button class="btn btn-success rounded-pill tag-btn p-2 flex-noshrink" id="tagBtn-tag1" data-tag="tag1" onclick="toggleTagSelection('tag1')">
        //   <span class="lighten">tag1</span>
        //   </button>
        inactiveTags.delete(tag);
        let tagButton = document.createElement("button");
        tagButton.classList.add("btn", "rounded-pill", "tag-btn", "p-2", "flex-noshrink", "active");
        tagButton.id = `nodeTagBtn-${tag}`;
        tagButton.setAttribute("data-tag", tag);
        tagButton.setAttribute("onclick", `toggleTagOnNode('${tag}')`);
        tagButton.style.background = stringToColor(tag);

        tagButton.innerHTML = `<span class="lighten">${tag}</span>`;
        tagContainer.appendChild(tagButton);
    });
    inactiveTags.forEach(inactiveTag => {
        let tagButton = document.createElement("button");
        tagButton.classList.add("btn", "rounded-pill", "tag-btn", "p-2", "flex-noshrink");
        tagButton.id = `nodeTagBtn-${inactiveTag}`;
        tagButton.setAttribute("data-tag", inactiveTag);
        tagButton.setAttribute("onclick", `toggleTagOnNode('${inactiveTag}')`);
        tagButton.style.background = stringToColor(inactiveTag);

        tagButton.innerHTML = `<span class="lighten">${inactiveTag}</span>`;
        tagContainer.appendChild(tagButton);
    });
    document.getElementById("editorTagContainer").hidden = false;

    editor = new JSONEditor(
        editorContainer,
        { schema: schema, startval: asset, disable_properties: true, show_errors: "always", theme: "bootstrap5", iconlib: "bootstrap" }
    );
    editor.on('ready', () => {
        hiddenEditors.forEach((value) => {
            let editorToHide = editor.getEditor(value);
            if (editorToHide !== undefined) {
                editorToHide.disable();
            }
            let editorContainer = document.querySelector(`[data-schemapath="${value}"]`);
            if (editorContainer !== null) {
                editorContainer.style.display = "none";
            }
        });
        disabledEditors.forEach((value) => {
            let editorToDisable = editor.getEditor(value);
            if (editorToDisable !== undefined) {
                editorToDisable.disable();
            }
        });
    });

    let notesEditorContainer = document.getElementById("notes-container");
    let notes = await fetch(`/forward/get_notes/${selectionType}/${selectionKey}`).then(response => response.text());
    notesEditor = new JSONEditor(notesEditorContainer, {
        schema: {
            "type": "string",
            "format": "markdown",
            "options": {
                "simplemde": {
                    "toolbar": [
                        "bold",
                        "italic",
                        "heading",
                        "|",
                        "link",
                        "quote",
                        "|",
                        "preview",
                        "guide"
                    ],
                    "spellChecker": false
                }
            }
        },
        startval: notes,
        placeholder: "Notes about the asset",
        theme: "bootstrap5",
        iconlib: "bootstrap"
    });
    return;
    $.getJSON('http://127.0.0.1:8000/models/' + networkElement.type, function (data) { console.log(data); }).done(function (data) {
        // JSON result in `data` variable
        var jsonSchema = {
            use_name_attributes: true,
            title: networkElement.type,
            schema: data["model_schema"]
        };

        console.log(data);

        var startVal;
        $.getJSON('http://127.0.0.1:5000/forward/get_asset/' + networkElement.type + '/' + networkElement.db_key, function (data) {
            return data;
        }).done(function (data) {
            console.log(data);
            startVal = data;
        });

        console.log(startVal);

        // reset editor holder
        let editorContainer = document.getElementById("json-editor-container");
        editorContainer.innerHTML = "";
        if (editor) {
            editor.destroy();
        }

        editor = new JSONEditor(
            editorContainer,
            { schema: jsonSchema, startval: networkElement, disable_properties: true, show_errors: "always", theme: "bootstrap5", iconlib: "bootstrap" }
        );

        editor.on('ready', function () {
            editor.validate();
            hiddenEditors = ['root.id', 'root.db_id', 'root.type', 'root.label', 'root.from', 'root.to'];
            hiddenEditors.forEach((value) => {
                let editorToHide = editor.getEditor(value);
                if (editorToHide !== undefined) {
                    editorToHide.disable();
                }
                let editorContainer = document.querySelector(`[data-schemapath="${value}"]`);
                if (editorContainer !== null) {
                    editorContainer.style.display = "none";
                }
            });
            disabledEditors = ['root.db_key', 'root.origin_id', 'root.target_id'];
            disabledEditors.forEach((value) => {
                let editorToDisable = editor.getEditor(value);
                if (editorToDisable !== undefined) {
                    editorToDisable.disable();
                }
            });
            for (const [key, value] of Object.entries(data["model_schema"]["properties"])) {
                try {
                    let actualKey = key;
                    switch (key) {
                        case "_key":
                        // actualKey = 'db' + key;
                        // break;
                        case "_id":
                            actualKey = 'db' + key;
                            break;
                        case "_from":
                            actualKey = 'origin_id';
                            break;
                        case "_to":
                            actualKey = 'target_id';
                            break;
                    }
                    let label = document.querySelector(`[data-schemapath="root.${actualKey}"] > label:first-of-type`);
                    console.log(key, value);
                    console.log(label);
                    console.log(actualKey);
                    let description = value.description != null ? value.description : value.title;
                    console.log(description);
                    label.title = description;
                    console.log(label.title);
                } catch (error) {

                }
            }
        });



        let errorContainer = document.getElementById("error-container");
        let resultContainer = document.getElementById("result-container");

        // editor.on("change", () => {
        //     console.log("editor change");
        //     console.log(editor.getValue());
        //     editor.validate();
        //     // var validationErrors = editor.validate();
        //     // if (validationErrors.length) {
        //     //     errorContainer.innerHTML = JSON.stringify(validationErrors, null, 2);
        //     // } else {
        //     //     errorContainer.innerHTML = 'valid';
        //     // }
        // });

        var saveButton = document.getElementById("save-btn");
        saveButton.hidden = false;
        var deleteButton = document.getElementById("delete-btn");
        deleteButton.hidden = false;

        deleteButton.addEventListener("click", function (event) {
            event.preventDefault();
            let json = editor.getValue();
            console.log(json);
            let assetType = json.type;
            let assetId = json.db_key;

            fetch('/forward/delete_asset/' + assetType + "/" + assetId, {
                method: 'POST',
            })
                .then(resp => resp.text())
                .then((html) => {
                    resultContainer.innerHTML = html;
                    console.log(html);

                    setTimeout(() => {
                        location.reload();
                    }, 1000);
                });
        });

        saveButton.addEventListener("click", function (event) {
            const errors = editor.validate();
            console.log(resultContainer);
            console.log(errors);
            if (errors.length) {
                const errorContainer = $("#json-editor-errors");
                errors.forEach((error) => {
                    const errorLine = document.createElement("p");
                    errorLine.innerHTML = error;
                    errorContainer.appendChild(errorLine);
                });
                return;
            }
            event.preventDefault();
            let json = editor.getValue();
            // Remove id and label from json, as they are not part of the schema
            delete json.id;
            delete json.label;
            console.log(json);
            fetch('/forward/update_asset/' + json.type, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(json)
            })
                .then(resp => resp.text())
                .then((html) => {
                    resultContainer.innerHTML = html;
                    console.log(html);
                    setTimeout(() => {
                        resultContainer.hidden = true;
                    }, 1000);
                });
            console.log(resultContainer);
        });

        var notesEditorContainer = document.getElementById("notes-container");
        var saveNotesButton = document.getElementById("save-notes-btn");
        notesEditor = new JSONEditor(notesEditorContainer, {
            schema: {
                "type": "string",
                "format": "markdown",
                "options": {
                    "simplemde": {
                        "toolbar": [
                            "bold",
                            "italic",
                            "heading",
                            "|",
                            "link",
                            "quote",
                            "|",
                            "preview",
                            "guide"
                        ],
                        "spellChecker": false
                    }
                }
            },
            placeholder: "Notes about the asset",
            theme: "bootstrap5",
            iconlib: "bootstrap"
        });
        notesEditor.on("ready", function () {
            console.log(notesEditor.editors.root);
            document.querySelector("#notes-container label").innerHTML = "Notes";
            document.getElementById("save-notes-btn").hidden = false;
            fetch('/forward/get_notes/' + networkElement.type + "/" + networkElement.db_key, {
                method: 'GET',
                headers: {
                    'Accept': 'text/plain'
                },
            })
                .then((resp) => resp.text())
                .then((notes) => {
                    return notes;
                }).then((notes) => {
                    notesEditor.editors.root.setValue(notes);
                });
        });
        saveNotesButton.addEventListener("click", function (event) {
            event.preventDefault();
            let notes = notesEditor.getValue();
            console.log(notes);
            fetch('/forward/set_notes/' + networkElement.type + "/" + networkElement.db_key, {
                method: 'POST',
                body: notes
            })
                .then(resp => resp.text())
                .then((notes) => {
                    document.getElementById("notes-saved").hidden = false;
                    setTimeout(() => {
                        document.getElementById("notes-saved").hidden = true;
                    }, 1000);
                });
        });
    }).fail(function () {
        console.log("error");
        document.getElementById("json-editor-container").innerHTML = "Error: Failed to load model";
        saveButton.hidden = true;
        deleteButton.hidden = true;
    });
}
