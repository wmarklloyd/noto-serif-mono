#include <stdio.h>
#include <stdlib.h>
#include <ft2build.h>
#include FT_FREETYPE_H
#include FT_MODULE_H
#include FT_DRIVER_H
/* usage: ftr font ppem mode interp gid...   mode: 0 unhinted gray, 1 hinted gray, 2 hinted mono */
int main(int argc,char**argv){
  FT_Library lib; FT_Face face; FT_Init_FreeType(&lib);
  FT_UInt iv=atoi(argv[4]); FT_Property_Set(lib,"truetype","interpreter-version",&iv);
  if(FT_New_Face(lib,argv[1],0,&face)) {fprintf(stderr,"face\n");return 1;}
  FT_Set_Char_Size(face,0,(FT_F26Dot6)(atof(argv[2])*64+0.5),72,72);
  int mode=atoi(argv[3]); int summary=0; if(mode>=10){summary=1;mode-=10;} int ped=0; if(mode>=4){ped=1;mode-=4;}
  for(int a=5;a<argc;a++){
    int gid=atoi(argv[a]);
    FT_Int32 fl=FT_LOAD_NO_AUTOHINT|FT_LOAD_NO_BITMAP;
    if(mode==0) fl|=FT_LOAD_NO_HINTING;
    if(mode==2) fl|=FT_LOAD_TARGET_MONO;
    if(ped) fl|=FT_LOAD_PEDANTIC;
    {FT_Error e=FT_Load_Glyph(face,gid,fl); if(e){printf("ERR %d %d\n",gid,e);continue;}}
    FT_Render_Glyph(face->glyph, mode==2?FT_RENDER_MODE_MONO:FT_RENDER_MODE_NORMAL);
    FT_Bitmap*b=&face->glyph->bitmap;
    if(summary){ /* first/last rows with any pixel >64, and ink */
      int first=-1,last=-1; long ink=0;
      for(unsigned r=0;r<b->rows;r++){int any=0; for(unsigned c=0;c<b->width;c++){int v=b->buffer[r*b->pitch+c]; ink+=v; if(v>64)any=1;} if(any){if(first<0)first=r; last=r;}}
      printf("S %d %d %d %ld %ld\n",gid,first<0?-999:face->glyph->bitmap_top-first,last<0?-999:face->glyph->bitmap_top-last-1,ink,face->glyph->advance.x); continue;}
    printf("G %d %d %d %d %d %ld\n",gid,face->glyph->bitmap_left,face->glyph->bitmap_top,b->width,b->rows,face->glyph->advance.x);
    for(unsigned r=0;r<b->rows;r++){
      for(unsigned c=0;c<b->width;c++){
        int v= mode==2 ? ((b->buffer[r*b->pitch+c/8]>>(7-c%8))&1)*255 : b->buffer[r*b->pitch+c];
        printf("%02x",v);
      }
      printf("\n");
    }
  }
  return 0;
}
