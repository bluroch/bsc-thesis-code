// function getSelectedTags() {
//     const tags = [];
//     document.querySelectorAll("#tagSelectorContainer > button[data-tag].active").forEach(btn => {
//         tags.push(btn.dataset.id);
//     });
//     return tags;
// }

// function getSelectedTypes() {
//     const types = [];
//     document.querySelectorAll("#typeSelectorContainer > button[data-type].active").forEach(btn => {
//         types.push(btn.dataset.id);
//     });
//     return types;
// }

function getFilteringData() {
    // let selectedTags = getSelectedTags();
    // let selectedTypes = getSelectedTypes();
    let tagInclusion = document.querySelector('input[name="tagInclusion"]:checked').value;
    let typeInclusion = document.querySelector('input[name="typeInclusion"]:checked').value;

    return { tags: Array.from(selectedTags), types: Array.from(selectedTypes), tag_filter_type: tagInclusion, type_filter_type: typeInclusion };
}

function refreshGraph() {
    const filtering = getFilteringData();
    console.log(filtering);
    console.log(JSON.stringify(filtering));
    fetch("/get_graph", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(filtering)
    })
        .then(response => response.json())
        .then(graphData => {
            const nodes = JSON.parse(graphData.nodes);
            const edges = JSON.parse(graphData.edges);
            console.log(JSON.parse(graphData.nodes));
            console.log(JSON.parse(graphData.edges));
            const newData = {nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges)};
            console.log(newData);
            network.setData(newData);
            // network_data.nodes = new vis.DataSet(graphData.nodes);
            // network_data.edges = new vis.DataSet(graphData.edges);
            // nodeCount = nodes.length;
            // edgeCount = edges.length;
            document.getElementById("nodeCount").innerText = nodes.length;
            document.getElementById("edgeCount").innerText = edges.length;
            // console.log(network_data);
            // Handle the response data
            // network.destroy();
            // console.log(graphContainer);
            // console.log(NETWORK_OPTIONS);
            // network = new vis.Network(graphContainer, network_data, NETWORK_OPTIONS);
            // console.log(network_data);

        })
        .catch(error => {
            // Handle any errors
            console.error(error);
        });
}