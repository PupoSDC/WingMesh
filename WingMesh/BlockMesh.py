import os

class BlockMesh:
    pointlist = [];
    hexblocks = [];
    boundlist = [];
    arclist   = [];
    mergepairs = [];

    # Adds a point to a point list only if it does not exist previously.
    def addPoint(self, point ):
        point = [
            float( '%.6f' % point[0] ),
            float( '%.6f' % point[1] ),
            float( '%.6f' % point[2] )
        ];
        if point not in self.pointlist: self.pointlist.append(point)
        return self.pointlist.index(point);

    # Creates one arc for the mesh between 2 points.
    def addArc( self, arc ):
        arc = [self.addPoint(arc[0]),self.addPoint(arc[1]),arc[2]];
        for x in self.arclist:
            if( x[0]==arc[0] and x[1]==arc[1] ): return self.arclist.index(x);
            if( x[1]==arc[0] and x[0]==arc[1] ): return self.arclist.index(x);
        self.arclist.append(arc)
        return self.arclist.index(arc);

    # Creates an HExablock between 8 points
    def addBlock( self, points, n_points, grade ):
        self.hexblocks.append([
            self.addPoint( points[0] ), self.addPoint( points[1] ),
            self.addPoint( points[2] ), self.addPoint( points[3] ),
            self.addPoint( points[4] ), self.addPoint( points[5] ),
            self.addPoint( points[6] ), self.addPoint( points[7] ),
            n_points, grade
        ]);

    def addMergePair( self, pair ):
        self.mergepairs.append( pair);

    # Adds a Face to the boundary list
    def addFace( self, name, points, type ):
        p_list = map( lambda x: self.addPoint(x), points );
        for face in self.boundlist:
            if face[0] == name:
                face[1].append( p_list );
                return;
        self.boundlist.append([name,[p_list],type]);

    # Prints out the blockMeshDict
    def write(self):
        blockMeshDict = open("system/blockMeshDict","w")

        # Write the heading
        blockMeshDict.write(
            "FoamFile\n{\n    version     2.0;\n" +
            "format      ascii;\n" +
            "class       dictionary;\n" +
            "object      blockMeshDict;\n}\n" +
            "convertToMeters 1;\n"
        );

        # Write down the vertices
        blockMeshDict.write( "\nvertices\n(\n")
        for point in self.pointlist:
            blockMeshDict.write(
                "    (" +
                repr( point[0] ) + " " +
                repr( point[1] ) + " " +
                repr( point[2] ) + ") // " +
                repr( self.pointlist.index(point) ) + "\n"
            );

        # Write down the blocks
        blockMeshDict.write( ");\n\nblocks\n(\n")
        for hex in self.hexblocks:
            blockMeshDict.write(
                "  hex ( " +
                repr(hex[0]) + " " +
                repr(hex[1]) + " " +
                repr(hex[2]) + " " +
                repr(hex[3]) + " " +
                repr(hex[4]) + " " +
                repr(hex[5]) + " " +
                repr(hex[6]) + " " +
                repr(hex[7]) + " ) (" +
                repr(hex[8][0]) + " " +
                repr(hex[8][1]) + " " +
                repr(hex[8][2]) + ") simpleGrading (" +
                repr(hex[9][0]) + " " +
                repr(hex[9][1]) + " " +
                repr(hex[9][2]) + ") // " +
                repr( self.hexblocks.index(hex) ) + " \n"
            );

        # Write down the edges
        blockMeshDict.write( ");\n\nedges\n(\n")
        for arc in self.arclist:
            blockMeshDict.write(
                "    arc " +  repr(arc[0]) + " " +  repr(arc[1]) + " ("
                + repr(arc[2][0]) + " "
                + repr(arc[2][1]) + " "
                + repr(arc[2][2]) + ") // " +
                repr( self.arclist.index(arc) ) + " \n"
            );

        # Write down the boundaries
        blockMeshDict.write( ");\n\nboundary\n(\n")
        for boundary in self.boundlist:
            faces = "";
            for face in boundary[1]:
                faces += "( "
                for point in face:
                    faces += " " + repr(point) + " ";
                faces += ")";
            blockMeshDict.write(
                "    "
                + boundary[0] + " { type "
                + boundary[2] + "; faces ("
                + faces       + ");}\n"
            );

        #write down merged patches
        blockMeshDict.write( ");\n\nmergePatchPairs\n(\n);\n")

        blockMeshDict.close()
        return;
