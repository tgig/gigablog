(function($){

    var Renderer = function(canvas){

        var canvas = $(canvas).get(0)
        var ctx = canvas.getContext("2d");
        //var gfx = arbor.Graphics(canvas);
        var particleSystem

        var folderName = "";
        var fileName = "";

        var that = {
            parameters: function(param, paramValue) {
                if (param == "folderName") {
                    folderName = paramValue;
                } else if (param == "fileName") {
                    fileName = paramValue;
                } else if (param == "canvasWidth") {
                    canvas.setAttribute('width', paramValue);
                } else if (param == "canvasHeight") {
                    canvas.setAttribute('height', paramValue);
                }
            },

            init:function(system){
                //
                // the particle system will call the init function once, right before the
                // first frame is to be drawn. it's a good place to set up the canvas and
                // to pass the canvas size to the particle system
                //
                // save a reference to the particle system for use in the .redraw() loop
                particleSystem = system

                // inform the system of the screen dimensions so it can map coords for us.
                // if the canvas is ever resized, screenSize should be called again with
                // the new dimensions
                particleSystem.screenSize(canvas.width, canvas.height) 
                particleSystem.screenPadding(80) // leave an extra 80px of whitespace per side
                
                // set up some event handlers to allow for node-dragging
                that.initMouseHandling()
            },
            
            redraw:function(){
                // 
                // redraw will be called repeatedly during the run whenever the node positions
                // change. the new positions for the nodes can be accessed by looking at the
                // .p attribute of a given node. however the p.x & p.y values are in the coordinates
                // of the particle system rather than the screen. you can either map them to
                // the screen yourself, or use the convenience iterators .eachNode (and .eachEdge)
                // which allow you to step through the actual node objects but also pass an
                // x,y point in the screen's coordinate system
                // 

                //gfx.clear()
                ctx.fillStyle = "#f2f2f2"
                ctx.fillRect(0,0, canvas.width, canvas.height)
                
                particleSystem.eachEdge(function(edge, pt1, pt2){
                    // edge: {source:Node, target:Node, length:#, data:{}}
                    // pt1:  {x:#, y:#}  source position in screen coords
                    // pt2:  {x:#, y:#}  target position in screen coords

                    // draw a line from pt1 to pt2
                    ctx.strokeStyle = "rgba(169,169,169, .333)"
                    ctx.lineWidth = 1
                    ctx.beginPath()
                    ctx.moveTo(pt1.x, pt1.y)
                    ctx.lineTo(pt2.x, pt2.y)
                    ctx.stroke()

                    //gfx.line(pt1, pt2, {stroke:"#A9A9A9", width:1})
                })

                particleSystem.eachNode(function(node, pt){
                    var w = 5;
                    if (node.mass > 1) {
                        w = 10;
                    }
                    
                    //if this is a regular node, then use the preset color
                    var fillColor = null;
                    if (node.data.color) {
                        fillColor = node.data.color
                    }
                    //if this is a leaf node then set a color
                    else {
                        fillColor = "#9C9C9C";
                        node.data.color = fillColor;
                        node.data.origColor = fillColor;
                        node.data.url = "/external-file/" + encodeURI(node.name);
                    }

                    ctx.fillStyle = fillColor;
                    ctx.beginPath();
                    ctx.arc(pt.x, pt.y, w, 0, 2 * Math.PI);
                    ctx.fill();

                })    			
            },

            switchSection: function (newSection, color) {
                
                node_hilite_color = "#000000"

                var parent = particleSystem.getNode(newSection)
                var children = $.map(particleSystem.getEdgesFrom(newSection), function (edge) {
                    return edge.target
                })

                //set parent color
                if (color == "color") {
                    parent.data.color = node_hilite_color;

                    let _folderName = parent.data.folderName || '[External]';
                    let _fileName = parent.data.fileName || parent.name;
                    $('#node-folder').text(_folderName);
                    $('#node-file').text(_fileName);
                }
                else if (color == "origColor") {
                    parent.data.color = parent.data.origColor
                    $('#node-folder').text(folderName);
                    $('#node-file').text(fileName);
                }

                //set children color
                particleSystem.eachNode(function (node) {

                    var nowVisible = ($.inArray(node, children) >= 0)
                    var newAlpha = (nowVisible) ? 1 : 0

                    if (color == "color" && newAlpha == 1) {
                        node.data.color = node_hilite_color
                    }
                    else if (color == "origColor") {
                        node.data.color = node.data.origColor
                    }
                })
            },
            
            initMouseHandling:function(){
                // no-nonsense drag and drop (thanks springy.js)
                var _selected = null;
                var _section = null;
                var _mousePosition = null;

                // set up a handler object that will initially listen for mousedowns then
                // for moves and mouseups while dragging
                var handler = {
                    moved:function(e){
                        var pos = $(canvas).offset();
                        _mouseP = arbor.Point(e.pageX-pos.left, e.pageY-pos.top)
                        nearest = particleSystem.nearest(_mouseP);

                        if (!nearest.node) return false

                        //when the mouse goes near a node make it purty
                        if (nearest.distance < 10) {

                            if (nearest.node.name!=_section) {
                                _section = nearest.node.name
                                that.switchSection(_section, "color")
                            }
                        }
                        // when the mouse goes away from a node, return to its original color
                        else if (_section) {
                            that.switchSection(_section, "origColor")
                            _section = null
                        }
                        
                        return false
                    },
                    clicked:function(e){
                        //set the _mousePosition here. When the mouseup event happens we'll check to see if the mouse moved
                        //  if it did not move, then throw window.location
                        _mousePosition = e.pageX + ' ' + e.pageY;

                        var pos = $(canvas).offset();
                        _mouseP = arbor.Point(e.pageX-pos.left, e.pageY-pos.top)
                        _selected = particleSystem.nearest(_mouseP);

                        if (_selected && _selected.node !== null){
                            // while we're dragging, don't let physics move the node
                            _selected.node.fixed = true
                        }

                        $(canvas).bind('mousemove', handler.dragged)
                        $(window).bind('mouseup', handler.dropped)

                        return false
                    },
                    dragged:function(e){
                        var pos = $(canvas).offset();
                        var s = arbor.Point(e.pageX-pos.left, e.pageY-pos.top)

                        if (_selected && _selected.node !== null){
                            var p = particleSystem.fromScreen(s)
                            _selected.node.p = p
                        }

                        return false
                    },

                    dropped:function(e){
                        if (_selected===null || _selected.node===undefined) return
                        if (_selected.node !== null) _selected.node.fixed = false

                        //if the _mousePosition did not change then see if we have a link to click
                        var currentMousePosition = e.pageX + ' ' + e.pageY;
                        if (currentMousePosition == _mousePosition) {
                            _mousePosition = null;
                            
                            //if this is a valid node then go to the page
                            if (_selected.node.data.url) {
                                window.location.href = '/miki/' + _selected.node.data.url
                            }
                        } else {
                            _mousePosition = null;
                        }

                        _selected.node.tempMass = 1000
                        _selected = null
                        $(canvas).unbind('mousemove', handler.dragged)
                        $(window).unbind('mouseup', handler.dropped)
                        _mouseP = null
                        return false
                    }
                }
                
                // start listening
                $(canvas).mousedown(handler.clicked);
                $(canvas).mousemove(handler.moved);

            },
            
            
        }
        return that
    }


    graph = (typeof(graph)!=='undefined') ? graph : {}
    $.extend(graph, {
        Renderer:Renderer
    });

})(this.jQuery)