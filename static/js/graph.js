
var GraphRenderer = function(svgId, graph, svgWidth, svgHeight, folderInfoDiv, fileInfoDiv) {

    document.getElementById(svgId).setAttribute('height', svgHeight);
    document.getElementById(svgId).setAttribute("width", svgWidth);

    var svg = d3.select("svg"),
        width = +svg.attr("width"),
        height = +svg.attr("height"),
        radius = 5
        folderInfo = document.getElementById(folderInfoDiv)
        fileInfo = document.getElementById(fileInfoDiv);

    if (folderInfo) {
        folderInfoParentText = folderInfo.textContent
    };
    if (fileInfo) {
        fileInfoParentText = fileInfo.textContent
    };

    var simulation = d3
        .forceSimulation()
        .force("link", d3.forceLink().id(function (d) {
                                            return d.id;
                                        }))
        .force("charge", d3.forceManyBody().strength(-50))
        .force("collision", d3.forceCollide().radius(radius + 4))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("x", d3.forceX(width / 2).strength(0.2))
        .force("y", d3.forceY(height / 2).strength(0.3));
    
    //I don't know why she swallowed the fly? But she fucking did and it doesn't work if she doesn't.
    setTimeout(function () {
        var link = svg
            .append("g")
            .attr("class", "links")
            .selectAll("line")
            .data(graph.links)
            .enter()
            .append("line");

        var node = svg
            .append("g")
            .attr("class", "nodes")
            .selectAll("circle")
            .data(graph.nodes)
            .enter()
            .append("circle")
            .attr("r", function (d) { return d.mass })
            .style("fill", function (d) {
                return d.color;
            })
            .call(
                d3
                    .drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended)
            );

        node.append("title").text(function (d) {
            return d.fileName;
        });

        node.on("click", function (node) {
            window.location.href = "/miki/" + node.url + ".html";
        });
        
        node.on("mouseover", function(d) {
            //if divs for folder/file display were passed in, then show the node we're moused-over
            if (folderInfo) {
                folderInfo.textContent = d.folderName;
            }
            if (fileInfo) {
                fileInfo.textContent = d.fileName;
            }
        })
        .on("mouseout", function(d) {
            if (folderInfo) {
                folderInfo.textContent = folderInfoParentText;
            }
            if (fileInfo) {
                fileInfo.textContent = fileInfoParentText;
            }
        });

        //simulation.nodes(graph.nodes).on("tick", ticked);
        simulation.nodes(graph.nodes).on("tick", function() {
            link.attr("x1", function (d) {
                return d.source.x;
            })
            .attr("y1", function (d) {
                return d.source.y;
            })
            .attr("x2", function (d) {
                return d.target.x;
            })
            .attr("y2", function (d) {
                return d.target.y;
            });

            node.attr("cx", function (d) {
                return (d.x = Math.max(radius, Math.min(width - radius, d.x)));
            }).attr("cy", function (d) {
                return (d.y = Math.max(radius, Math.min(height - radius, d.y)));
            });
        })

        simulation.force("link").links(graph.links).strength(3);

        
    }, 1000);

    function dragstarted(d) {
        if (!d3.event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(d) {
        d.fx = d3.event.x;
        d.fy = d3.event.y;
    }

    function dragended(d) {
        if (!d3.event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }


}

