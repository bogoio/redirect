/*
  SelecionarRebarbas.ms  -  3ds Max 2026
  Seleciona faces pontudas ("rebarbas") nas bordas abertas de um Editable Poly.

  Uma face e considerada rebarba quando toca a borda aberta E:
    - tem um angulo interno muito agudo (triangulo-agulha), ou
    - tem 2+ arestas abertas (face pendurada, presa por uma aresta so), ou
    - dobra muito em relacao as vizinhas (aba saindo da superficie).

  Uso: selecione o objeto, rode o script (Scripting > Run Script) e ajuste os valores.
*/
(
	fn interiorMinAngle obj f =
	(
		local vs = polyop.getFaceVerts obj f
		local n = vs.count
		local minA = 180.0
		for i = 1 to n do
		(
			local p  = polyop.getVert obj vs[i]
			local pa = polyop.getVert obj vs[if i == 1 then n else i - 1]
			local pb = polyop.getVert obj vs[if i == n then 1 else i + 1]
			local a = pa - p
			local b = pb - p
			if length a > 1e-6 and length b > 1e-6 do
			(
				local d = dot (normalize a) (normalize b)
				d = amax -1.0 (amin 1.0 d)
				local ang = acos d
				if ang < minA do minA = ang
			)
		)
		minA
	)

	fn findSpikes obj maxAng useAng useDangling useDihedral maxDih =
	(
		local openE = polyop.getOpenEdges obj
		local result = #{}
		local nf = polyop.getNumFaces obj
		for f = 1 to nf do
		(
			local fe = polyop.getFaceEdges obj f
			local nOpen = 0
			for e in fe where openE[e] do nOpen += 1
			if nOpen > 0 do
			(
				local hit = false
				if useDangling and nOpen >= 2 do hit = true
				if not hit and useAng and (interiorMinAngle obj f) < maxAng do hit = true
				if not hit and useDihedral do
				(
					local nrm = polyop.getFaceNormal obj f
					for e in fe where not openE[e] and not hit do
						for g in (polyop.getEdgeFaces obj e) where g != f do
						(
							local d = amax -1.0 (amin 1.0 (dot nrm (polyop.getFaceNormal obj g)))
							if acos d > maxDih do hit = true
						)
				)
				if hit do result[f] = true
			)
		)
		result
	)

	try (destroyDialog roRebarbas) catch ()
	rollout roRebarbas "Selecionar Rebarbas"
	(
		checkbox chkAng "Angulo agudo" checked:true
		spinner spAng "  max (graus):" range:[1, 90, 20] type:#float
		checkbox chkDang "Faces penduradas (2+ arestas abertas)" checked:true
		checkbox chkDih "Dobra forte com vizinha" checked:false
		spinner spDih "  min (graus):" range:[1, 180, 70] type:#float
		checkbox chkGrow "Crescer selecao ao longo da borda" checked:false
		button btnGo "Selecionar" width:150 height:28
		label lblInfo ""

		on btnGo pressed do
		(
			local obj = selection[1]
			if obj == undefined then (messageBox "Selecione um objeto."; return ok)
			if classOf obj.baseObject != Editable_Poly do
			(
				if not queryBox "O objeto sera convertido para Editable Poly. Continuar?" do return ok
				convertToPoly obj
			)
			if obj.modifiers.count > 0 do (messageBox "Colapse os modificadores antes."; return ok)

			local sel = findSpikes obj spAng.value chkAng.checked chkDang.checked chkDih.checked spDih.value
			if chkGrow.checked do
			(
				local openE = polyop.getOpenEdges obj
				local vs = polyop.getVertsUsingFace obj sel
				local ext = (polyop.getFacesUsingVert obj vs) * (polyop.getFacesUsingEdge obj openE)
				sel = sel + ext
			)

			max modify mode
			modPanel.setCurrentObject obj.baseObject
			subObjectLevel = 4
			polyop.setFaceSelection obj sel
			redrawViews()
			lblInfo.text = (sel.numberSet as string) + " faces selecionadas"
		)
	)
	createDialog roRebarbas 240 200
)
