const LINKS=[["index.html","Início"],["calendario.html","Calendário"],["corridas.html","Corridas"],["pilotos.html","Pilotos"],["equipes.html","Equipes"],["campeoes.html","Campeões"]];
const NAC={British:"Reino Unido",Dutch:"Países Baixos",Italian:"Itália",Monegasque:"Mônaco",Australian:"Austrália",French:"França","New Zealander":"Nova Zelândia",Argentine:"Argentina",German:"Alemanha",Brazilian:"Brasil",Spanish:"Espanha",Thai:"Tailândia",Japanese:"Japão",Canadian:"Canadá",Finnish:"Finlândia",Mexican:"México"};
function corEquipe(n){
  n=(n||"").toLowerCase();
  const m=[["mercedes","#27c4aa"],["ferrari","#e8002d"],["mclaren","#ff8000"],["racing","#6692ff"],["rb f1","#6692ff"],["red bull","#3671c6"],["alpine","#ff87bc"],["haas","#9a9ea5"],["audi","#d6224a"],["williams","#37bedd"],["aston","#229971"],["cadillac","#8a8a99"]];
  for(const [k,c] of m) if(n.includes(k)) return c;
  return "#888";
}
const lerDados=async n=>(await fetch("dados/"+n)).json();
document.addEventListener("DOMContentLoaded",()=>{
  const atual=location.pathname.split("/").pop()||"index.html";
  const h=document.createElement("header");
  h.className="topo";
  h.innerHTML='<div class="in"><a class="marca" href="index.html">F1 <b>BRASIL</b></a><nav>'+LINKS.map(([u,t])=>'<a href="'+u+'"'+(u===atual?' class="on"':"")+'>'+t+'</a>').join("")+'</nav></div>';
  document.body.prepend(h);
});
