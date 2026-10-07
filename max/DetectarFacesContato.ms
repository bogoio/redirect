/*  DetectarFacesContato.ms  -  3ds Max 2026
    Seleciona as faces do objeto A que tocam (ou atravessam) o objeto B,
    e opcionalmente as faces de B que tocam A.
    Uso: Scripting > Run Script, escolha A e B, ajuste a tolerancia e clique Detectar.
*/

try (destroyDialog roContato) catch()

rollout roContato "Faces em contato" width:240
(
    local nodeFilt = fn nodeFilt o = superClassOf o == GeometryClass

    pickbutton pbA "Escolher objeto A" width:200 filter:nodeFilt autoDisplay:true
    pickbutton pbB "Escolher objeto B" width:200 filter:nodeFilt autoDisplay:true
    spinner spTol "Tolerancia (unid.):" range:[0,1e6,0.5] type:#worldunits
    spinner spDepth "Penetracao max.:" range:[0,1e6,50] type:#worldunits
    spinner spMinV "Min. vertices perto:" range:[1,4,1] type:#integer
    checkbox chkCenter "Testar tambem o centro da face" checked:true
    checkbox chkBoth "Selecionar tambem em B" checked:true
    checkbox chkDetach "Destacar faces de A num objeto novo" checked:false
    button btGo "Detectar" width:200 height:28
    label lbInfo "" width:220 height:30

    -- true se o ponto p esta a menos de tol da superficie, ou dentro dela ate depth
    fn pontoToca mpi meshB p tol depth =
    (
        if not (mpi.closestFace p doubleSided:true) do return false
        local d = mpi.getHitDist()
        if d <= tol do return true
        if d > depth do return false
        -- ponto mais proximo e normal para saber se esta dentro de B
        local f = mpi.getHitFace() + 1
        local b = mpi.getHitBary()
        local fv = getFace meshB f
        local hit = (getVert meshB fv.x)*b.x + (getVert meshB fv.y)*b.y + (getVert meshB fv.z)*b.z
        dot (p - hit) (getFaceNormal meshB f) < 0
    )

    -- devolve bitarray das faces de 'src' que tocam 'dst'
    fn facesQueTocam src dst tol depth minV useCenter =
    (
        if classOf src != Editable_Poly do convertToPoly src
        local meshB = snapshotAsMesh dst
        local mpi = MeshProjIntersect()
        mpi.setNode dst
        mpi.build()

        local nV = polyop.getNumVerts src
        local vOk = #{}
        vOk.count = nV
        for v = 1 to nV do
            if pontoToca mpi meshB (polyop.getVert src v) tol depth do vOk[v] = true

        local res = #{}
        for f = 1 to polyop.getNumFaces src do
        (
            local n = 0
            for v in (polyop.getFaceVerts src f) where vOk[v] do n += 1
            if n >= minV or (useCenter and pontoToca mpi meshB (polyop.getFaceCenter src f) tol depth) do
                res[f] = true
        )
        mpi.free()
        delete meshB
        res
    )

    on btGo pressed do
    (
        local a = pbA.object, b = pbB.object
        if not isValidNode a or not isValidNode b or a == b do
        (
            messageBox "Escolha dois objetos diferentes."
            return false
        )
        local t0 = timeStamp()
        local fa, fb = #{}
        undo "Faces em contato" on
        (
            fa = facesQueTocam a b spTol.value spDepth.value spMinV.value chkCenter.checked
            polyop.setFaceSelection a fa
            if chkBoth.checked do
            (
                fb = facesQueTocam b a spTol.value spDepth.value spMinV.value chkCenter.checked
                polyop.setFaceSelection b fb
            )
            if chkDetach.checked and not fa.isEmpty do
            (
                local nome = uniqueName (a.name + "_contato")
                polyop.detachFaces a fa delete:false asNode:true name:nome
            )
        )
        select a
        max modify mode
        subObjectLevel = 4
        redrawViews()
        lbInfo.text = "A: " + fa.numberSet as string + " faces | B: " + fb.numberSet as string + \
                      " faces\n" + ((timeStamp() - t0) / 1000.0) as string + " s"
    )
)
createDialog roContato
