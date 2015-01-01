Xflow.registerOperator("xflow.blenderSun", {
    outputs: [  {type: 'float3', name: 'intensity'}],
    params:  [  {type: 'float3', source: 'color'},
                {type: 'float', source: 'energy'}],
    evaluate: function(result, value1, value2, info) {
        throw new Error("Not used!");
    },
    evaluate_core: function(intensity, color, energy){
        intensity[0] = color[0] * energy[0];
        intensity[1] = color[1] * energy[0];
        intensity[2] = color[2] * energy[0];
    }
});

Xflow.registerOperator("xflow.blenderSpot", {
    outputs: [  {type: 'float3', name: 'intensity'}],
    params:  [  {type: 'float3', source: 'color'},
                {type: 'float', source: 'energy'}],
    evaluate: function(result, value1, value2, info) {
        throw new Error("Not used!");
    },
    evaluate_core: function(intensity, color, energy){
        intensity[0] = color[0] * energy[0];
        intensity[1] = color[1] * energy[0];
        intensity[2] = color[2] * energy[0];
    }
});


Xflow.registerOperator("xflow.blenderPoint", {
    outputs: [  {type: 'float3', name: 'intensity'}],
    params:  [  {type: 'float3', source: 'color'},
                {type: 'float', source: 'energy'}],
    evaluate: function(result, value1, value2, info) {
        throw new Error("Not used!");
    },
    evaluate_core: function(intensity, color, energy){
        intensity[0] = color[0] * energy[0];
        intensity[1] = color[1] * energy[0];
        intensity[2] = color[2] * energy[0];
    }
});

Xflow.registerOperator("xflow.blenderMaterial", {
    outputs: [
                {type: 'float3', name: 'diffuseColor'},
                {type: 'float3', name: 'specularColor'},
                {type: 'float', name: 'shininess'},
                {type: 'float', name: 'transparency'}
             ],
    params:  [
                {type: 'float3', source: 'diffuse_color'},
                {type: 'float', source: 'diffuse_intensity'},
                {type: 'float3', source: 'specular_color'},
                {type: 'float', source: 'specular_intensity'},
                {type: 'float', source: 'specular_hardness'},
                {type: 'float', source: 'alpha'}
            ],
    evaluate: function(result, value1, value2, info) {
        throw new Error("Not used!");
    },
    evaluate_core: function(diffuseColor, specularColor, shininess, transparency, diffuse_color, diffuse_intensity, specular_color, specular_intensity, specular_hardness, alpha){
        diffuseColor[0] = diffuse_color[0] * diffuse_intensity[0];
        diffuseColor[1] = diffuse_color[1] * diffuse_intensity[0];
        diffuseColor[2] = diffuse_color[2] * diffuse_intensity[0];
        specularColor[0] = specular_color[0] * specular_intensity[0];
        specularColor[1] = specular_color[1] * specular_intensity[0];
        specularColor[2] = specular_color[2] * specular_intensity[0];
        shininess[0] = specular_hardness[0] / 511;
        transparency[0] = Math.max(0, 1 - alpha[0]);
    }
});