/*
 * Palette Graphique - prélude au projet multimodal 3A SRI
 * 4 objets gérés : cercle, rectangle(carré), losange et triangle
 * (c) 05/11/2019
 * Dernière révision : 28/04/2020
 */
 
import java.awt.Point;
import fr.dgac.ivy.*;

Ivy bus;


ArrayList<Forme> formes; // liste de formes stockées
FSM mae; // Finite Sate Machine
int indice_forme;
PImage sketch_icon;


void setup() {
  size(800,600);
  surface.setResizable(true);
  surface.setTitle("Palette multimodale");
  surface.setLocation(20,20);
  sketch_icon = loadImage("Palette.jpg");
  surface.setIcon(sketch_icon);
  
  formes= new ArrayList(); // nous créons une liste vide
  noStroke();
  mae = FSM.INITIAL;
  indice_forme = -1;
  try {
    bus = new Ivy("Palette", "Palette is ready", null);
    bus.start("127.0.0.1:2010");
      bus.bindMsg("FUSION: ACTION=(.*) WHERE=(.*) FORME=(.*) COULEUR=(.*) LOCALISATION=(.*) COORDONNES=(.*)", 
  new IvyMessageListener() {
    public void receive(IvyClient client, String[] args) {
      handleFusion(args[0], args[2], args[3], args[5]);
    }
});
  } catch (IvyException ie) {
    println("Erreur Ivy : " + ie.getMessage());
  }
}

void draw() {
  background(0);
  //println("MAE : " + mae + " indice forme active ; " + indice_forme);
  switch (mae) {
    case INITIAL:  // Etat INITIAL
      background(255);
      fill(0);
      text("Etat initial (c(ercle)/l(osange)/r(ectangle)/t(riangle) pour créer la forme à la position courante)", 50,50);
      text("m(ove)+ click pour sélectionner un objet et click pour sa nouvelle position", 50,80);
      text("click sur un objet pour changer sa couleur de manière aléatoire", 50,110);
      break;
      
    case AFFICHER_FORMES:  // 
    case DEPLACER_FORMES_SELECTION: 
    case DEPLACER_FORMES_DESTINATION: 
      affiche();
      break;   
      
    default:
      break;
  }  
}

// fonction d'affichage des formes m
void affiche() {
  background(255);
  /* afficher tous les objets */
  for (int i=0;i<formes.size();i++) // on affiche les objets de la liste
    (formes.get(i)).update();
}

void mousePressed() { // sur l'événement clic
  Point p = new Point(mouseX,mouseY);
  boolean cliqueSurForme = false; 
  
  switch (mae) {
    case AFFICHER_FORMES:
      for (int i=0;i<formes.size();i++) { // we're trying every object in the list
      } 
      break;
      
   case DEPLACER_FORMES_SELECTION:
     for (int i=0;i<formes.size();i++) { // we're trying every object in the list        
        if ((formes.get(i)).isClicked(p)) {
          cliqueSurForme = true; 
          indice_forme = i;
          mae = FSM.DEPLACER_FORMES_DESTINATION;
        }         
     }
     if (indice_forme == -1)
       mae= FSM.AFFICHER_FORMES;
     break;
     
   case DEPLACER_FORMES_DESTINATION:
     if (indice_forme !=-1)
       (formes.get(indice_forme)).setLocation(new Point(mouseX,mouseY));
     indice_forme=-1;
     mae=FSM.AFFICHER_FORMES;
     break;
     
    default:
      break;
  }
  if (bus != null) {
    String type = cliqueSurForme ? "forme" : "vide";
    try {
      bus.sendMsg("Palette Click type=" + type + " x=" + mouseX + " y=" + mouseY);
    } catch (IvyException ie) {
      println("Erreur envoi Ivy : " + ie.getMessage());
    }
  }
}


void keyPressed() {
  Point p = new Point(mouseX,mouseY);
  switch(key) {
    case 'r':
      Forme f= new Rectangle(p);
      formes.add(f);
      mae=FSM.AFFICHER_FORMES;
      break;
      
    case 'c':
      Forme f2=new Circle(p);
      formes.add(f2);
      mae=FSM.AFFICHER_FORMES;
      break;
    
    case 't':
      Forme f3=new Triangle(p);
      formes.add(f3);
       mae=FSM.AFFICHER_FORMES;
      break;  
      
    case 'l':
      Forme f4=new Diamond(p);
      formes.add(f4);
      mae=FSM.AFFICHER_FORMES;
      break;
      
      case 'a':
      Forme f5=new Square(p);
      formes.add(f5);
      mae=FSM.AFFICHER_FORMES;
      break;
      
      
    case 'm' : // move
      mae=FSM.DEPLACER_FORMES_SELECTION;
      break;
  }
}

void handleFusion(String action, String forme, String couleur, String coordString) {

  ArrayList<Point> coords = new ArrayList<Point>();

try {
    // Remove all brackets
    coordString = coordString.replace("[", "").replace("]", "");

    // Now split into coordinate pairs: "607, 359, 611, 275"
    String[] nums = coordString.split(",");

    // Should always be even: x1,y1,x2,y2,...
    for (int i = 0; i + 1 < nums.length; i += 2) {
        int x = int(nums[i].trim());
        int y = int(nums[i+1].trim());
        coords.add(new Point(x, y));
        println(">>> coords = " + x + "," + y);
    }

} catch(Exception e) {
    println("Error parsing coords: " + coordString);
}

  println(">>> FUSION RECUE action=" + action + " forme=" + forme + " couleur=" + couleur + " coords=" + coords);

  // ---------------------------------------------------------------------
  // 1) CREATE
  // ---------------------------------------------------------------------
  if (action.equalsIgnoreCase("CREATE")) {

    if (coords.size() < 1) return;

    Point p = coords.get(0);
    Forme f = null;

    switch(forme.toUpperCase()) {
      case "CIRCLE":  f = new Circle(p);  break;
      case "RECTANGLE": f = new Rectangle(p); break;
      case "TRIANGLE": f = new Triangle(p); break;
      case "SQUARE": f = new Square(p); break;
      case "DIAMOND":  f = new Diamond(p); break;
    }

    if (f != null) {
      if (!couleur.equals("") && !couleur.equals("undefined"))
        f.setColor(colorFromName(couleur));
      formes.add(f);
      mae = FSM.AFFICHER_FORMES;
    }
  }

// ---------------------------------------------------------------------
// 2) DELETE
// ---------------------------------------------------------------------
else if (action.equalsIgnoreCase("DELETE")) {

  Forme target = null;

  // ------------------------------------------------------------
  // A) DELETE coords
  // ------------------------------------------------------------
  if (coords.size() > 0) {
    Point p = coords.get(0);
    for (Forme f : formes) {
      if (f.isClicked(p)) {
        target = f;
        break;
      }
    }
  }

  // ------------------------------------------------------------
  // B) DELETE couleur + forme (seulement si non AMBIGU)
  // ------------------------------------------------------------
  else if (!forme.equals("undefined")&& !couleur.equals("undefined")) {
    

    ArrayList<Forme> matches = new ArrayList<Forme>();

    for (Forme f : formes) {
      println(f);
      // compare la forme et la couleur
      if (f.getClass().getSimpleName().equalsIgnoreCase(forme)
          && approxColor(f.getColor(), colorFromName(couleur))) {
        matches.add(f);
      }
    }
    println(matches.size());

    if (matches.size() > 1) {
      println(">>> DELETE ABANDON — ambigu (" + matches.size() + " correspondances)");
      return;
    }
      if (matches.size() == 1){
      target = matches.get(0);
    }
  }

  
  else if (!forme.equals("undefined")){
    

    ArrayList<Forme> matches = new ArrayList<Forme>();

    for (Forme f : formes) {
      println(f);
      // compare la forme
      if (f.getClass().getSimpleName().equalsIgnoreCase(forme)) {
        matches.add(f);
      }
    }
    println(matches.size());

    if (matches.size() > 1) {
        println(">>> DELETE ABANDON — ambigu (" + matches.size() + " correspondances)");
      return;
    }

    if (matches.size() == 1){
      target = matches.get(0);
    }
  }

  else if (!couleur.equals("undefined")){
    
    

    ArrayList<Forme> matches = new ArrayList<Forme>();

    for (Forme f : formes) {
      println(f);
      // compare la couleur
      if (approxColor(f.getColor(), colorFromName(couleur))) {
        matches.add(f);
      }
    }
    println(matches.size());

    if (matches.size() > 1) {
        println(">>> DELETE ABANDON — ambigu (" + matches.size() + " correspondances)");
      return;
    }

    if (matches.size() == 1){
      target = matches.get(0);
    }
  }

  // ------------------------------------------------------------
  // Final deletion
  // ------------------------------------------------------------
  if (target != null) {
    formes.remove(target);
    mae = FSM.AFFICHER_FORMES;
  }
}

  // ---------------------------------------------------------------------
  // 3) MOVE 
  // ---------------------------------------------------------------------
  else if (action.equalsIgnoreCase("MOVE")) {
    Forme target = null;
    
  // ---------------------------------------------------------------------
  // A) MOVE : coord 1 → coord 2
  // ---------------------------------------------------------------------
    if (coords.size() > 2){

      Point source = coords.get(0);
      Point dest = coords.get(1);
  
      for (Forme f : formes) {
        if (f.isClicked(source)) {
          f.setLocation(dest);
          mae = FSM.AFFICHER_FORMES;
          break;
        }
      }
    }
  // ------------------------------------------------------------
  // B) MOVE forme (seulement si non AMBIGU)
  // ------------------------------------------------------------
    else if (coords.size()==1 && !forme.equals("undefined")){
       ArrayList<Forme> matches = new ArrayList<Forme>();
       
      for (Forme f : formes) {
        println(f);
        // compare la forme et la couleur
        if (f.getClass().getSimpleName().equalsIgnoreCase(forme)) {
          matches.add(f);
        }
      }
      println(matches.size());
  
      if (matches.size() > 1) {
        println(">>> MOVE ABANDON — ambigu (" + matches.size() + " correspondances)");
        return;
      }
        if (matches.size() == 1){
          target = matches.get(0);
      }
       
    }
    // ------------------------------------------------------------
    // C) MOVE couleur (seulement si non AMBIGU)
    // ------------------------------------------------------------
    else if (coords.size()==1 && !couleur.equals("undefined")){
       ArrayList<Forme> matches = new ArrayList<Forme>();
      
      for (Forme f : formes) {
        println(f);
        // compare la forme et la couleur
        if (approxColor(f.getColor(), colorFromName(couleur))) {
          matches.add(f);
        }
      }
      println(matches.size());
  
      if (matches.size() > 1) {
        println(">>> MOVE ABANDON — ambigu (" + matches.size() + " correspondances)");
        return;
      }
        if (matches.size() == 1){
          target = matches.get(0);
      }
    }
    // ------------------------------------------------------------
    // D) MOVE forme et couleur (seulement si non AMBIGU)
    // ------------------------------------------------------------
    else if (coords.size()==1 && !forme.equals("undefined") && !couleur.equals("undefined")){
       ArrayList<Forme> matches = new ArrayList<Forme>();
       
      for (Forme f : formes) {
        println(f);
        // compare la forme et la couleur
        if (f.getClass().getSimpleName().equalsIgnoreCase(forme)
            && approxColor(f.getColor(), colorFromName(couleur))) {
          matches.add(f);
        }
      }
      println(matches.size());
  
      if (matches.size() > 1) {
        println(">>> DELETE ABANDON — ambigu (" + matches.size() + " correspondances)");
        return;
      }
        if (matches.size() == 1){
          target = matches.get(0);
      }
    }
    if (targer!=null){
      target.setLocation(coords.get(0));
      mae = FSM.AFFICHER_FORMES;
    }
    
  }
}


color colorFromName(String name) {
  if (name == null) return color(200);

  switch(name.toUpperCase()) {
    case "RED":
      return color(255, 0, 0);

    case "ORANGE":
      return color(255, 128, 0);

    case "YELLOW":
      return color(255, 255, 0);

    case "GREEN":
      return color(0, 255, 0);

    case "BLUE":
      return color(0, 0, 255);

    case "PURPLE":
      return color(160, 32, 240);  // vivid purple

    case "DARK":
      return color(30, 30, 30);    // nearly black
  }

  // default neutral gray
  return color(200, 200, 200);
}


boolean approxColor(color c1, color c2) {
  return abs(red(c1)-red(c2)) < 40 &&
         abs(green(c1)-green(c2)) < 40 &&
         abs(blue(c1)-blue(c2)) < 40;
}
