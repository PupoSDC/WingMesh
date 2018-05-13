#!/usr/bin/env python
import os
import math
import copy


################################################################################
## FUNCTION DEFINITIONS ########################################################
################################################################################

# Reads a 2D array aerofoil point index, and converts it to a 3D point array
def readAerofoil( file, position, scale ):
    response = [];
    with open(file,'r') as file:
        for line in file:
            response.append( map( float, line.split() ) )
            response[-1][0] = response[-1][0] * scale + position[0];
            response[-1][1] = response[-1][1] * scale + position[1];
            response[-1].append( position[2] );
    return response;

# Calculates the intermediate section between 2 sections.
def mixSections( section_1, section_2, percentage ):
    response = [];
    for i in range(0, len(section_1) ):
        response.append([
            section_1[i][0] + (section_2[i][0] - section_1[i][0]) * percentage,
            section_1[i][1] + (section_2[i][1] - section_1[i][1]) * percentage,
            section_1[i][2] + (section_2[i][2] - section_1[i][2]) * percentage
        ]);
    return response;

#distorts a wing section by a linear interpolation of 2 aerofoils.
def distortSection( section_1, section_2, p_start, p_end ):
    response = [];
    length  = section_1[ len(section_1) / 2 + 1 ][0] - section_1[0][0];
    d_start = section_1[ len(section_1) / 2 + 1 ][0] - p_start * length;
    d_end   = section_1[ len(section_1) / 2 + 1 ][0] - p_end   * length;
    for i in range(0, len(section_1) ):
        percentage = 0;
        if( section_1[i][0] > d_start ):
            percentage = (section_1[i][0] - d_start) / (d_end - d_start);
        response.append([
            section_1[i][0] + (section_2[i][0] - section_1[i][0]) * percentage,
            section_1[i][1] + (section_2[i][1] - section_1[i][1]) * percentage,
            section_1[i][2] + (section_2[i][2] - section_1[i][2]) * percentage
        ]);
    return response;

# Creates a wing section
def makeWingSection( block_mesh, sec_1, sec_2, p_cut, radius, points, grade ):
    length   = sec_1[ len(sec_1) / 2 + 1 ][0] - sec_1[0][0];
    d_cut    = sec_1[0][0] + p_cut * length;
    n_trails = 0;
    ps       = range(0,8);
    sp       = range(0,8);

    # count trailing edges
    for i in range( 0, len(sec_1)/2 ):
        if sec_1[i][0] > d_cut: n_trails += 1;

    # Add Main wing sections
    for i in range( 0, len(sec_1)/2  ):
        a_i = ( float(i+0) / float(len(sec_1)-1)*1.5 - 0.25 ) * math.pi / 1.0;
        a_j = ( float(i+1) / float(len(sec_1)-1)*1.5 - 0.25 ) * math.pi / 1.0;

        ps[0] = sec_1[i+1];
        ps[1] = sec_1[i+0];
        ps[2] = [ -radius*math.sin(a_i), radius*math.cos(a_i), sec_1[i+0][2] ];
        ps[3] = [ -radius*math.sin(a_j), radius*math.cos(a_j), sec_1[i+1][2] ];
        ps[4] = sec_2[i+1];
        ps[5] = sec_2[i+0];
        ps[6] = [ -radius*math.sin(a_i), radius*math.cos(a_i), sec_2[i+0][2] ];
        ps[7] = [ -radius*math.sin(a_j), radius*math.cos(a_j), sec_2[i+1][2] ];
        sp[0] = sec_2[-i-2];
        sp[1] = sec_2[-i-1];
        sp[2] = [ -radius*math.sin(a_i), -radius*math.cos(a_i), sec_2[-i-1][2] ];
        sp[3] = [ -radius*math.sin(a_j), -radius*math.cos(a_j), sec_2[-i-2][2] ];
        sp[4] = sec_1[-i-2];
        sp[5] = sec_1[-i-1];
        sp[6] = [ -radius*math.sin(a_i), -radius*math.cos(a_i), sec_1[-i-1][2] ];
        sp[7] = [ -radius*math.sin(a_j), -radius*math.cos(a_j), sec_1[-i-2][2] ];

        if( sec_1[0][2] > 0.0 ):
            ps[2][2] += 0.1; ps[3][2] += 0.1; ps[6][2] += 0.1; ps[7][2] += 0.1;
            sp[2][2] += 0.1; sp[3][2] += 0.1; sp[6][2] += 0.1; sp[7][2] += 0.1;
        else:
            ps[6][2] += 0.1; ps[7][2] += 0.1;
            sp[2][2] += 0.1; sp[3][2] += 0.1;

        # Create main outer wing blocks and free stream boundaries
        block_mesh.addBlock( ps, points, grade );
        block_mesh.addBlock( sp, points, grade );
        block_mesh.addFace( "freestream", [ ps[2],ps[3],ps[6],ps[7]], "patch" );
        block_mesh.addFace( "freestream", [ sp[2],sp[3],sp[6],sp[7]], "patch" );
        # Add left surfaces if first section
        if sec_1[0][2] == 0.0:
            block_mesh.addFace("left", [ps[3],ps[2],ps[1],ps[0]], "symmetry");
            block_mesh.addFace("left", [sp[4],sp[5],sp[6],sp[7]], "symmetry");
        # Create inside of the wing blocks (if necessary)
        if( i < n_trails ):
            block_mesh.addBlock(
                [ sp[4],sp[5],ps[1],ps[0], sp[0],sp[1],ps[5],ps[4] ],
                [ points[0], 1, points[2] ],
                [ 1, 1, 1 ]
            );
            block_mesh.addFace("wing", [sp[4],sp[5],ps[1],ps[0]], "wall" );
            block_mesh.addFace("wing", [sp[0],sp[1],ps[5],ps[4]], "wall" );
        if( i >= n_trails ):
            block_mesh.addFace("wing", [ps[5],ps[4],ps[1],ps[0]], "wall" );
            block_mesh.addFace("wing", [sp[0],sp[1],sp[5],sp[4]], "wall" );
        if( i == n_trails and i != 0 ):
            block_mesh.addFace("wing", [ sp[5], sp[1], ps[5], ps[1] ], "wall");

    #  Add Trailing edge
    for i in range( 0, len(sec_1)/8 ):
        a_i   = ( - float(i+1) / float( len(sec_1)/8 )*0.25 - 0.25 ) * math.pi;
        a_j   = ( - float(i+0) / float( len(sec_1)/8 )*0.25 - 0.25 ) * math.pi;
        ps[0] = sec_1[0];
        ps[1] = sec_1[0];
        ps[2] = [ -radius*math.sin(a_i), radius*math.cos(a_i), sec_1[0][2] ];
        ps[3] = [ -radius*math.sin(a_j), radius*math.cos(a_j), sec_1[0][2] ];
        ps[4] = sec_2[0];
        ps[5] = sec_2[0];
        ps[6] = [ -radius*math.sin(a_i), radius*math.cos(a_i), sec_2[0][2] ];
        ps[7] = [ -radius*math.sin(a_j), radius*math.cos(a_j), sec_2[0][2] ];
        sp[0] = sec_2[0];
        sp[1] = sec_2[0];
        sp[2] = [ -radius*math.sin(a_i), -radius*math.cos(a_i), sec_2[0][2] ];
        sp[3] = [ -radius*math.sin(a_j), -radius*math.cos(a_j), sec_2[0][2] ];
        sp[4] = sec_1[0];
        sp[5] = sec_1[0];
        sp[6] = [ -radius*math.sin(a_i), -radius*math.cos(a_i), sec_1[0][2] ];
        sp[7] = [ -radius*math.sin(a_j), -radius*math.cos(a_j), sec_1[0][2] ];

        if( sec_1[0][2] > 0.0 ):
            ps[2][2] += 0.1; ps[3][2] += 0.1; ps[6][2] += 0.1; ps[7][2] += 0.1;
            sp[2][2] += 0.1; sp[3][2] += 0.1; sp[6][2] += 0.1; sp[7][2] += 0.1;
        else:
            ps[6][2] += 0.1; ps[7][2] += 0.1;
            sp[2][2] += 0.1; sp[3][2] += 0.1;

        block_mesh.addBlock( ps, points, grade );
        block_mesh.addBlock( sp, points, grade );
        block_mesh.addFace( "freestream", [ ps[2],ps[3],ps[6],ps[7]], "patch" );
        block_mesh.addFace( "freestream", [ sp[2],sp[3],sp[6],sp[7]], "patch" );
        # Add left surfaces if first section
        if sec_1[0][2] == 0.0:
            block_mesh.addFace("left", [ps[3],ps[2],ps[1],ps[0]], "symmetry");
            block_mesh.addFace("left", [sp[4],sp[5],sp[6],sp[7]], "symmetry");

#Creates a winglet section.
def makeWinglet( block_mesh, section, radius, points, grade ):
    ps = range(0,8);
    for i in range(0, len(section)/2 ):
        # calculate  auxiliary values for the first section
        c_x_i = ( section[-i-1][0] + section[i][0] ) / 2.0;
        c_y_i = ( section[-i-1][1] + section[i][1] ) / 2.0;
        c_z_i = ( section[-i-1][2] + section[i][2] ) / 2.0;
        r_w_i = abs( section[-i-1][1] - section[i][1] ) / 2.0;
        a_i   = ( float(i+0) / float(len(section)-1)*1.5 - 0.25 ) * math.pi

        # calculate auxiliary values for the second section
        c_x_j = ( section[-i-2][0] + section[i+1][0] ) / 2.0;
        c_y_j = ( section[-i-2][1] + section[i+1][1] ) / 2.0;
        c_z_j = ( section[-i-2][2] + section[i+1][2] ) / 2.0;
        r_w_j = abs( section[-i-2][1] - section[i+1][1] ) / 2.0;
        a_j   = ( float(i+1) / float(len(section)-1)*1.5 - 0.25 ) * math.pi;

        # Allocate points
        ps[0] = section[i+1];
        ps[1] = section[i+0];
        ps[2] = [ -radius*math.sin(a_i),  radius*math.cos(a_i), section[i+0][2] + 0.1 ];
        ps[3] = [ -radius*math.sin(a_j),  radius*math.cos(a_j), section[i+1][2] + 0.1 ];
        ps[4] = section[-i-2];
        ps[5] = section[-i-1];
        ps[6] = [ -radius*math.sin(a_i), -radius*math.cos(a_i), section[i+0][2] + 0.1 ];
        ps[7] = [ -radius*math.sin(a_j), -radius*math.cos(a_j), section[i+1][2] + 0.1 ];

        # Create centre points.
        w_0 = [ c_x_i, c_y_i, c_z_i + r_w_i ];
        w_1 = [ c_x_j, c_y_j, c_z_j + r_w_j ];
        w_2 = [ -radius* math.sin( a_i ), 0, c_z_i + radius * math.cos( a_i ) ];
        w_3 = [ -radius* math.sin( a_j ), 0, c_z_j + radius * math.cos( a_j ) ];

        # Create blocks and faces
        block_mesh.addBlock( ps, points, grade );
        if( r_w_i > 0 ): block_mesh.addArc( [ ps[1],ps[5], w_0 ] );
        if( r_w_j > 0 ): block_mesh.addArc( [ ps[0],ps[4], w_1 ] );
        if( i < len(section)/2-1 ): block_mesh.addArc( [ ps[2],ps[6], w_2 ] );
        if( i < len(section)/2-1 ): block_mesh.addArc( [ ps[3],ps[7], w_3 ] );

        block_mesh.addFace("freestream", [ps[2],ps[3],ps[7],ps[6]], "patch");
        block_mesh.addFace("wing",       [ps[0],ps[1],ps[5],ps[4]], "wall");

    #  Add Trailing edge
    for i in range( 0, len(section)/8 ):
        a_i = ( - float(i+1) / float( len(section)/8 )*0.25 - 0.25 ) * math.pi;
        a_j = ( - float(i+0) / float( len(section)/8 )*0.25 - 0.25 ) * math.pi;
        w_0 = [ -radius*math.sin(a_j), 0, section[0][2]+radius*math.cos(a_j) ];

        ps[0] = section[0];
        ps[1] = section[0];
        ps[2] = [ -radius*math.sin(a_i),  radius*math.cos(a_i), section[0][2] + 0.1 ];
        ps[3] = [ -radius*math.sin(a_j),  radius*math.cos(a_j), section[1][2] + 0.1 ];
        ps[4] = section[0];
        ps[5] = section[0];
        ps[6] = [ -radius*math.sin(a_i), -radius*math.cos(a_i), section[0][2] + 0.1 ];
        ps[7] = [ -radius*math.sin(a_j), -radius*math.cos(a_j), section[0][2] + 0.1 ];

        block_mesh.addBlock( ps, points, grade );
        block_mesh.addArc( [ ps[3],ps[7], w_0 ] );
        block_mesh.addFace("freestream", [ps[2],ps[3],ps[7],ps[6]], "patch");

################################################################################
## Script ######################################################################
################################################################################

block_mesh = BlockMesh();

root  = readAerofoil('sources/NACA/2411', [ -0.958, 0.0,   0.0   ], 2.143 );
tip   = readAerofoil('sources/NACA/2411', [ -0.473, 0.109, 4.215 ], 1.050 );
#tip_b = readAerofoil('sources/NACA/2411', [ -0.395, 0.109, 4.265 ], 0.877 );
#tip_c = readAerofoil('sources/NACA/2411', [ -0.260, 0.109, 4.300 ], 0.577 );
#mid_a = mixSections(root,tip_a,0.544);
#mid_b = mixSections(root,tip_a,0.560);
#mid   = distortSection( mid_a, mid_b, 0.75, 1.0 );
#tip   = distortSection( tip_a, tip_b, 0.75, 1.0 );

makeWingSection(
    block_mesh,
    root,
    tip,
    0.0,
    15.0,
    [1,20,30],  # 30,20
    [1,100,1]
);

#makeWinglet( #winglet radius should be 135
#   block_mesh,
#   tip,
#   15.0,
#   [1,20,20],    # 1,20
#   [1,100,1]  # 1000
#);

block_mesh.write();
os.system('blockMesh')
