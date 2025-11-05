/*
 * Braille Display - 
 * (c) 19/10/2021
 * Dernière révision : 19/10/2021
 */
import fr.dgac.ivy.*;
import java.text.Normalizer;

Ivy bus;
PFont f,ftitle;
String message;
PImage sketch_icon;


void setup(){
  size(390,160); // 10 caractères Braille x 48 
  surface.setTitle("Braille display");
  surface.setLocation(50,50);
  sketch_icon = loadImage("braille.jpg");
  surface.setIcon(sketch_icon);
  
  // load Fonts 
  f=loadFont("Braille3D-48.vlw");
  ftitle=loadFont("Parisine-Bold-24.vlw");  
  // ivy bus
  try {
    bus = new Ivy("Braille_display", " Braille_display is ready", null);
    bus.start("127.255.255.255:2010");
    bus.bindMsg("^Braille_display Text=(.*)", new IvyMessageListener() {
      public void receive(IvyClient client,String[] args) {
        message = Normalizer.normalize(args[0], Normalizer.Form.NFKD);
        message = message.toUpperCase();

        println(message);
        
        if (message.length()>10)
          message=message.substring(0,9); // limit display to 9 characters
        try {
          bus.sendMsg("Braille_display Characters_displayed="+message.length());
        }
        catch (IvyException ie) {};
      }              
    });  
  }
  catch (IvyException ie) {};  
  message =""; // empty message at the beginning
}

void draw(){
  background(255);
  fill(60,255,50);
  textFont(ftitle,24); // police Parisine
  textAlign(CENTER,ENTER);
  text("-- Plage braille 10 points -- ",width/2,30);
  
  textFont(f); // police Braille
  textAlign(LEFT, CENTER);
  fill(0);
  text(message, 10, 80);
}
