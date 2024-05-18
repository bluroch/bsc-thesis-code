// function onTagSelectionUpdate() {
//     selectedTags =
// }
let creationFormEditor;

let selectedType;

const DISABLED_ASSET_CREATION_FIELDS = ["root._id"];

async function openAssetCreatorForm() {
    selectedType = document.getElementById("assetCreationSelector").value;
    console.log(selectedType);
    let formContainer = document.getElementById('assetCreatorFormContainer');
    formContainer.innerHTML = "";
    if (creationFormEditor) {
        creationFormEditor.destroy();
    }
    let model = await fetch(`/forward/get_model/${selectedType}`).then(response => response.json()).then(data => {
        let schema = data["model_schema"];
        creationFormEditor = new JSONEditor(
            formContainer,
            { schema: schema, disable_properties: true, show_errors: "always", theme: "bootstrap5", iconlib: "bootstrap" }
        );
    });

    creationFormEditor.on('ready', () => {
        creationFormEditor.validate();
        DISABLED_ASSET_CREATION_FIELDS.forEach((field) => {
            let editorToDisable = creationFormEditor.getEditor(field);
            if (editorToDisable !== undefined) {
                editorToDisable.disable();
            }
        });
    });

    formContainer.style.display = 'block';
}

async function openEdgeCreatorForm() {
    selectedType = document.getElementById("edgeCreationSelector").value;
    console.log(selectedType);
    let formContainer = document.getElementById('edgeCreatorFormContainer');
    formContainer.innerHTML = "";
    if (creationFormEditor) {
        creationFormEditor.destroy();
    }
    let model = await fetch(`/forward/get_model/${selectedType}`).then(response => response.json()).then(data => {
        let schema = data["model_schema"];
        creationFormEditor = new JSONEditor(
            formContainer,
            { schema: schema, disable_properties: true, show_errors: "always", theme: "bootstrap5", iconlib: "bootstrap" }
        );
    });

    creationFormEditor.on('ready', () => {
        creationFormEditor.validate();
        DISABLED_ASSET_CREATION_FIELDS.forEach((field) => {
            let editorToDisable = creationFormEditor.getEditor(field);
            if (editorToDisable !== undefined) {
                editorToDisable.disable();
            }
        });
    });

    formContainer.style.display = 'block';
}


async function createAsset(editor) {
    let values = editor.getValue();
    delete values._id;
    let errors = editor.validate();
    // console.log(creationFormEditor.getValue());
    if (values._key == "") {
        alert("The key cannot be empty!");
    }
    if (!errors.length) {
        await fetch(`/forward/create_asset/${selectedType}`, {
            method: 'POST', body: JSON.stringify(values) }).then(resp => resp.text()).then(resp => console.log(resp));
        setTimeout(() => {
            location.reload();
        }, 1000);
    }
}

// async function deleteAsset() {

// }
