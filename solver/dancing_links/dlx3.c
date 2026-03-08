#define o mems++
#define oo mems+= 2
#define ooo mems+= 3
#define O "%"
#define mod % \

#define max_level 500
#define max_cols 10000
#define max_nodes 100000000
#define bufsize (9*max_cols+3)  \

#define show_basics 1
#define show_choices 2
#define show_details 4
#define show_profile 128
#define show_full_state 256
#define show_tots 512
#define show_warnings 1024 \

#define len itm
#define aux color \

#define root 0 \

#define sanity_checking 0 \

#define panic(m) {fprintf(stderr,""O"s!\n"O"d: "O".99s\n",m,p,buf) ;exit(-666) ;} \

#define infty max_nodes \

/*2:*/
#line 89 "dlx3.w"

#include <stdio.h> 
#include <stdlib.h> 
#include <string.h> 
#include <ctype.h> 
#include "gb_flip.h"
typedef unsigned int uint;
typedef unsigned long long ullng;
/*7:*/
#line 291 "dlx3.w"

typedef struct node_struct{
int up,down;
int itm;
int color;
}node;

/*:7*//*8:*/
#line 324 "dlx3.w"

typedef struct itm_struct{
char name[8];
int prev,next;
int bound,slack;
}item;

/*:8*/
#line 97 "dlx3.w"
;
/*3:*/
#line 164 "dlx3.w"

int random_seed= 0;
int randomizing;
int vbose= show_basics+show_warnings;
int spacing;
int show_choices_max= 1000000;
int show_choices_gap= 1000000;

int show_levels_max= 1000000;
int maxl= 0;
char buf[bufsize];
ullng count;
ullng options;
ullng imems,mems,cmems,tmems;
ullng updates;
ullng cleansings;
ullng bytes;
ullng nodes;
ullng thresh= 10000000000;
ullng delta= 10000000000;
ullng maxcount= 0xffffffffffffffff;
ullng timeout= 0x1fffffffffffffff;
FILE*shape_file;
char*shape_name;

/*:3*//*9:*/
#line 331 "dlx3.w"

node nd[max_nodes];
int last_node;
item cl[max_cols+2];
int second= max_cols;
int last_itm;

/*:9*//*27:*/
#line 669 "dlx3.w"

int level;
int choice[max_level];
ullng profile[max_level];
int first_tweak[max_level];
int scor[max_level];

/*:27*/
#line 98 "dlx3.w"
;
/*11:*/
#line 349 "dlx3.w"

void print_option(int p,FILE*stream,int head,int score){
register int k,q;
if((p<last_itm&&p==head)||(head>=last_itm&&p==nd[head].itm))
fprintf(stream," null "O".8s",cl[p].name);
else{
if(p<last_itm||p>=last_node||nd[p].itm<=0){
fprintf(stderr,"Illegal option "O"d!\n",p);
return;
}
for(q= p;;){
fprintf(stream," "O".8s",cl[nd[q].itm].name);
if(nd[q].color)
fprintf(stream,":"O"c",nd[q].color> 0?nd[q].color:nd[nd[q].itm].color);
q++;
if(nd[q].itm<=0)q= nd[q].up;

if(q==p)break;
}
}
for(q= head,k= 1;q!=p;k++){
if(p>=last_itm&&q==nd[p].itm){
fprintf(stream," (?)\n");return;
}else q= nd[q].down;
}
fprintf(stream," ("O"d of "O"d)\n",k,score);
}

void prow(int p){
print_option(p,stderr,nd[nd[p].itm].down,nd[nd[p].itm].len);
}

/*:11*//*12:*/
#line 383 "dlx3.w"

void print_itm(int c){
register int p;
if(c<root||c>=last_itm){
fprintf(stderr,"Illegal item "O"d!\n",c);
return;
}
fprintf(stderr,"Item "O".8s",cl[c].name);
if(c<second){
if(cl[c].slack||cl[c].bound!=1)
fprintf(stderr," ("O"d,"O"d)",cl[c].bound-cl[c].slack,cl[c].bound);
fprintf(stderr,", length "O"d, neighbors "O".8s and "O".8s:\n",
nd[c].len,cl[cl[c].prev].name,cl[cl[c].next].name);
}else fprintf(stderr,", length "O"d:\n",nd[c].len);
for(p= nd[c].down;p>=last_itm;p= nd[p].down)prow(p);
}

/*:12*//*13:*/
#line 405 "dlx3.w"

void sanity(void){
register int k,p,q,pp,qq,t;
for(q= root,p= cl[q].next;;q= p,p= cl[p].next){
if(cl[p].prev!=q)fprintf(stderr,"Bad prev field at itm "O".8s!\n",
cl[p].name);
if(p==root)break;
/*14:*/
#line 416 "dlx3.w"

for(qq= p,pp= nd[qq].down,k= 0;;qq= pp,pp= nd[pp].down,k++){
if(nd[pp].up!=qq)fprintf(stderr,"Bad up field at node "O"d!\n",pp);
if(pp==p)break;
if(nd[pp].itm!=p)fprintf(stderr,"Bad itm field at node "O"d!\n",pp);
}
if(nd[p].len!=k)fprintf(stderr,"Bad len field in item "O".8s!\n",
cl[p].name);

/*:14*/
#line 412 "dlx3.w"
;
}
}

/*:13*//*34:*/
#line 752 "dlx3.w"

void cover(int c,int deact){
register int cc,l,r,rr,nn,uu,dd,t;
if(deact){
o,l= cl[c].prev,r= cl[c].next;
oo,cl[l].next= r,cl[r].prev= l;
}
updates++;
for(o,rr= nd[c].down;rr>=last_itm;o,rr= nd[rr].down)
for(nn= rr+1;nn!=rr;){
if(o,nd[nn].color>=0){
o,uu= nd[nn].up,dd= nd[nn].down;
cc= nd[nn].itm;
if(cc<=0){
nn= uu;
continue;
}
oo,nd[uu].down= dd,nd[dd].up= uu;
updates++;
o,t= nd[cc].len-1;
o,nd[cc].len= t;
}
nn++;
}
}

/*:34*//*35:*/
#line 787 "dlx3.w"

void uncover(int c,int react){
register int cc,l,r,rr,nn,uu,dd,t;
for(o,rr= nd[c].down;rr>=last_itm;o,rr= nd[rr].down)
for(nn= rr+1;nn!=rr;){
if(o,nd[nn].color>=0){
o,uu= nd[nn].up,dd= nd[nn].down;
cc= nd[nn].itm;
if(cc<=0){
nn= uu;
continue;
}
oo,nd[uu].down= nd[dd].up= nn;
o,t= nd[cc].len+1;
o,nd[cc].len= t;
}
nn++;
}
if(react){
o,l= cl[c].prev,r= cl[c].next;
oo,cl[l].next= cl[r].prev= c;
}
}

/*:35*//*38:*/
#line 851 "dlx3.w"

void purify(int p){
register int cc,rr,nn,uu,dd,t,x;
o,cc= nd[p].itm,x= nd[p].color;
nd[cc].color= x;
cleansings++;
for(o,rr= nd[cc].down;rr>=last_itm;o,rr= nd[rr].down){
if(o,nd[rr].color!=x){
for(nn= rr+1;nn!=rr;){
o,uu= nd[nn].up,dd= nd[nn].down;
o,cc= nd[nn].itm;
if(cc<=0){
nn= uu;continue;
}
if(nd[nn].color>=0){
oo,nd[uu].down= dd,nd[dd].up= uu;
updates++;
o,t= nd[cc].len-1;
o,nd[cc].len= t;
}
nn++;
}
}else if(rr!=p)cleansings++,o,nd[rr].color= -1;
}
}

/*:38*//*39:*/
#line 880 "dlx3.w"

void unpurify(int p){
register int cc,rr,nn,uu,dd,t,x;
o,cc= nd[p].itm,x= nd[p].color;
for(o,rr= nd[cc].up;rr>=last_itm;o,rr= nd[rr].up){
if(o,nd[rr].color<0)o,nd[rr].color= x;
else if(rr!=p){
for(nn= rr-1;nn!=rr;){
o,uu= nd[nn].up,dd= nd[nn].down;
o,cc= nd[nn].itm;
if(cc<=0){
nn= dd;continue;
}
if(nd[nn].color>=0){
oo,nd[uu].down= nd[dd].up= nn;
o,t= nd[cc].len+1;
o,nd[cc].len= t;
}
nn--;
}
}
}
}

/*:39*//*40:*/
#line 913 "dlx3.w"

void tweak(int n,int block){
register int cc,nn,uu,dd,t;
for(nn= (block?n+1:n);;){
if(o,nd[nn].color>=0){
o,uu= nd[nn].up,dd= nd[nn].down;
cc= nd[nn].itm;
if(cc<=0){
nn= uu;
continue;
}
oo,nd[uu].down= dd,nd[dd].up= uu;
updates++;
o,t= nd[cc].len-1;
o,nd[cc].len= t;
}
if(nn==n)break;
nn++;
}
}

/*:40*//*41:*/
#line 949 "dlx3.w"

void untweak(int c,int x,int unblock){
register int z,cc,nn,uu,dd,t,k,rr,qq;
oo,z= nd[c].down,nd[c].down= x;
for(rr= x,k= 0,qq= c;rr!=z;o,qq= rr,rr= nd[rr].down){
o,nd[rr].up= qq,k++;
if(unblock)for(nn= rr+1;nn!=rr;){
if(o,nd[nn].color>=0){
o,uu= nd[nn].up,dd= nd[nn].down;
cc= nd[nn].itm;
if(cc<=0){
nn= uu;
continue;
}
oo,nd[uu].down= nd[dd].up= nn;
o,t= nd[cc].len+1;
o,nd[cc].len= t;
}
nn++;
}
}
o,nd[rr].up= qq;
oo,nd[c].len+= k;
if(!unblock)uncover(c,0);
}

/*:41*//*45:*/
#line 1074 "dlx3.w"

void print_state(void){
register int l,p,c,q;
fprintf(stderr,"Current state (level "O"d):\n",level);
for(l= 0;l<level;l++){
p= choice[l];
c= (p<last_itm?p:nd[p].itm);
if(!first_tweak[l])print_option(p,stderr,nd[c].down,scor[l]);
else print_option(p,stderr,first_tweak[l],scor[l]);
if(l>=show_levels_max){
fprintf(stderr," ...\n");
break;
}
}
fprintf(stderr," "O"lld sols, "O"lld mems, and max level "O"d so far.\n",
count,mems,maxl);
}

/*:45*//*46:*/
#line 1112 "dlx3.w"

void print_progress(void){
register int l,k,d,c,p;
register double f,fd;
fprintf(stderr," after "O"lld mems: "O"lld sols,",mems,count);
for(f= 0.0,fd= 1.0,l= 0;l<level;l++){
p= choice[l],d= scor[l];
c= (p<last_itm?p:nd[p].itm);
if(!first_tweak[l])p= nd[c].down;
else p= first_tweak[l];
for(k= 1;p!=choice[l];k++,p= nd[p].down);
fd*= d,f+= (k-1)/fd;
fprintf(stderr," "O"c"O"c",
k<10?'0'+k:k<36?'a'+k-10:k<62?'A'+k-36:'*',
d<10?'0'+d:d<36?'a'+d-10:d<62?'A'+d-36:'*');
if(l>=show_levels_max){
fprintf(stderr,"...");
break;
}
}
fprintf(stderr," "O".5f\n",f+0.5/fd);
}

/*:46*/
#line 99 "dlx3.w"
;
main(int argc,char*argv[]){
register int cc,i,j,k,p,pp,q,r,s,t,
cur_node,best_itm,stage,score,best_s,best_l;
/*4:*/
#line 192 "dlx3.w"

for(j= argc-1,k= 0;j;j--)switch(argv[j][0]){
case'v':k|= (sscanf(argv[j]+1,""O"d",&vbose)-1);break;
case'm':k|= (sscanf(argv[j]+1,""O"d",&spacing)-1);break;
case's':k|= (sscanf(argv[j]+1,""O"d",&random_seed)-1),randomizing= 1;break;
case'd':k|= (sscanf(argv[j]+1,""O"lld",&delta)-1),thresh= delta;break;
case'c':k|= (sscanf(argv[j]+1,""O"d",&show_choices_max)-1);break;
case'C':k|= (sscanf(argv[j]+1,""O"d",&show_levels_max)-1);break;
case'l':k|= (sscanf(argv[j]+1,""O"d",&show_choices_gap)-1);break;
case't':k|= (sscanf(argv[j]+1,""O"lld",&maxcount)-1);break;
case'T':k|= (sscanf(argv[j]+1,""O"lld",&timeout)-1);break;
case'S':shape_name= argv[j]+1,shape_file= fopen(shape_name,"w");
if(!shape_file)
fprintf(stderr,"Sorry, I can't open file `"O"s' for writing!\n",
shape_name);
break;
default:k= 1;
}
if(k){
fprintf(stderr,"Usage: "O"s [v<n>] [m<n>] [s<n>] [d<n>]"
" [c<n>] [C<n>] [l<n>] [t<n>] [T<n>] [S<bar>] < foo.dlx\n",
argv[0]);
exit(-1);
}
if(randomizing)gb_init_rand(random_seed);

/*:4*/
#line 103 "dlx3.w"
;
/*15:*/
#line 430 "dlx3.w"

if(max_nodes<=2*max_cols){
fprintf(stderr,"Recompile me: max_nodes must exceed twice max_cols!\n");
exit(-999);
}
while(1){
if(!fgets(buf,bufsize,stdin))break;
if(o,buf[p= strlen(buf)-1]!='\n')panic("Input line way too long");
for(p= 0;o,isspace(buf[p]);p++);
if(buf[p]=='|'||!buf[p])continue;
last_itm= 1;
break;
}
if(!last_itm)panic("No items");
for(;o,buf[p];){
/*16:*/
#line 459 "dlx3.w"

if(second==max_cols)stage= 0;else stage= 2;
start_name:for(j= 0;j<8&&(o,!isspace(buf[p+j]));j++){
if(buf[p+j]==':'){
if(stage)panic("Illegal `:' in item name");
/*17:*/
#line 487 "dlx3.w"

for(q= 0,pp= p;pp<p+j;pp++){
if(buf[pp]<'0'||buf[pp]> '9')panic("Illegal digit in bound spec");
q= 10*q+buf[pp]-'0';
}
p= pp+1;
while(j)cl[last_itm].name[--j]= 0;

/*:17*/
#line 464 "dlx3.w"
;
r= q,stage= 1;
goto start_name;
}else if(buf[p+j]=='|'){
if(stage> 1)panic("Illegal `|' in item name");
/*17:*/
#line 487 "dlx3.w"

for(q= 0,pp= p;pp<p+j;pp++){
if(buf[pp]<'0'||buf[pp]> '9')panic("Illegal digit in bound spec");
q= 10*q+buf[pp]-'0';
}
p= pp+1;
while(j)cl[last_itm].name[--j]= 0;

/*:17*/
#line 469 "dlx3.w"
;
if(q==0)panic("Upper bound is zero");
if(stage==0)r= q;
else if(r> q)panic("Lower bound exceeds upper bound");
stage= 2;
goto start_name;
}
o,cl[last_itm].name[j]= buf[p+j];
}
switch(stage){
case 1:panic("Lower bound without upper bound");
case 0:q= r= 1;
case 2:break;
}
if(j==0)panic("Item name empty");
if(j==8&&!isspace(buf[p+j]))panic("Item name too long");
/*18:*/
#line 495 "dlx3.w"

for(k= 1;o,strncmp(cl[k].name,cl[last_itm].name,8);k++);
if(k<last_itm)panic("Duplicate item name");

/*:18*/
#line 485 "dlx3.w"
;

/*:16*/
#line 445 "dlx3.w"
;
/*19:*/
#line 499 "dlx3.w"

if(last_itm> max_cols)panic("Too many items");
if(second==max_cols)
oo,cl[last_itm-1].next= last_itm,cl[last_itm].prev= last_itm-1,
o,cl[last_itm].bound= q,cl[last_itm].slack= q-r;
else o,cl[last_itm].next= cl[last_itm].prev= last_itm;
o,nd[last_itm].up= nd[last_itm].down= last_itm;

last_itm++;

/*:19*/
#line 446 "dlx3.w"
;
for(p+= j+1;o,isspace(buf[p]);p++);
if(buf[p]=='|'){
if(second!=max_cols)panic("Item name line contains | twice");
second= last_itm;
for(p++;o,isspace(buf[p]);p++);
}
}
if(second==max_cols)second= last_itm;
o,cl[root].prev= second-1;
last_node= last_itm;
o,nd[last_node].itm= 0;

/*:15*/
#line 104 "dlx3.w"
;
/*20:*/
#line 512 "dlx3.w"

while(1){
if(!fgets(buf,bufsize,stdin))break;
if(o,buf[p= strlen(buf)-1]!='\n')panic("Option line too long");
for(p= 0;o,isspace(buf[p]);p++);
if(buf[p]=='|'||!buf[p])continue;
i= last_node;
for(pp= 0;buf[p];){
for(j= 0;j<8&&(o,!isspace(buf[p+j]))&&buf[p+j]!=':';j++)
o,cl[last_itm].name[j]= buf[p+j];
if(!j)panic("Empty item name");
if(j==8&&!isspace(buf[p+j])&&buf[p+j]!=':')
panic("Item name too long");
if(j<8)o,cl[last_itm].name[j]= '\0';
/*21:*/
#line 553 "dlx3.w"

for(k= 0;o,strncmp(cl[k].name,cl[last_itm].name,8);k++);
if(k==last_itm)panic("Unknown item name");
if(o,nd[k].aux>=i)panic("Duplicate item name in this option");
last_node++;
if(last_node==max_nodes)panic("Too many nodes");
o,nd[last_node].itm= k;
if(k<second)pp= 1;
o,t= nd[k].len+1;
/*22:*/
#line 575 "dlx3.w"

o,nd[k].len= t;
nd[k].aux= last_node;
if(!randomizing){
o,r= nd[k].up;
ooo,nd[r].down= nd[k].up= last_node,nd[last_node].up= r,nd[last_node].down= k;
}else{
mems+= 4,t= gb_unif_rand(t);
for(o,r= k;t;o,r= nd[r].down,t--);
ooo,q= nd[r].up,nd[q].down= nd[r].up= last_node;
o,nd[last_node].up= q,nd[last_node].down= r;
}

/*:22*/
#line 562 "dlx3.w"
;

/*:21*/
#line 526 "dlx3.w"
;
if(buf[p+j]!=':')o,nd[last_node].color= 0;
else if(k>=second){
if((o,isspace(buf[p+j+1]))||(o,!isspace(buf[p+j+2])))
panic("Color must be a single character");
o,nd[last_node].color= (unsigned char)buf[p+j+1];
p+= 2;
}else panic("Primary item must be uncolored");
for(p+= j+1;o,isspace(buf[p]);p++);
}
if(!pp){
if(vbose&show_warnings)
fprintf(stderr,"Option ignored (no primary items): "O"s",buf);
while(last_node> i){
/*23:*/
#line 588 "dlx3.w"

o,k= nd[last_node].itm;
oo,nd[k].len--,nd[k].aux= i-1;
o,q= nd[last_node].up,r= nd[last_node].down;
oo,nd[q].down= r,nd[r].up= q;

/*:23*/
#line 540 "dlx3.w"
;
last_node--;
}
}else{
o,nd[i].down= last_node;
last_node++;
if(last_node==max_nodes)panic("Too many nodes");
options++;
o,nd[last_node].up= i+1;
o,nd[last_node].itm= -options;
}
}

/*:20*/
#line 105 "dlx3.w"
;
if(vbose&show_basics)
/*24:*/
#line 594 "dlx3.w"

fprintf(stderr,
"("O"lld options, "O"d+"O"d items, "O"d entries successfully read)\n",
options,second-1,last_itm-second,last_node-last_itm);

/*:24*/
#line 107 "dlx3.w"
;
if(vbose&show_tots)
/*25:*/
#line 603 "dlx3.w"

{
fprintf(stderr,"Item totals:");
for(k= 1;k<last_itm;k++){
if(k==second)fprintf(stderr," |");
fprintf(stderr," "O"d",nd[k].len);
}
fprintf(stderr,"\n");
}

/*:25*/
#line 109 "dlx3.w"
;
imems= mems,mems= 0;
/*26:*/
#line 637 "dlx3.w"

level= 0;
forward:nodes++;
if(vbose&show_profile)profile[level]++;
if(sanity_checking)sanity();
/*28:*/
#line 676 "dlx3.w"

if(delta&&(mems>=thresh)){
thresh+= delta;
if(vbose&show_full_state)print_state();
else print_progress();
}
if(mems>=timeout){
fprintf(stderr,"TIMEOUT!\n");goto done;
}

/*:28*/
#line 642 "dlx3.w"
;
/*42:*/
#line 1013 "dlx3.w"

score= infty,tmems= mems;
if((vbose&show_details)&&
level<show_choices_max&&level>=maxl-show_choices_gap)
fprintf(stderr,"Level "O"d:",level);
for(o,k= cl[root].next;k!=root;o,k= cl[k].next){
o,s= cl[k].slack;if(s> cl[k].bound)s= cl[k].bound;
if((vbose&show_details)&&
level<show_choices_max&&level>=maxl-show_choices_gap){
if(cl[k].bound!=1||s!=0)fprintf(stderr," "O".8s("O"d:"O"d,"O"d)",
cl[k].name,cl[k].bound-s,cl[k].bound,
nd[k].len+s-cl[k].bound+1);
else fprintf(stderr," "O".8s("O"d)",cl[k].name,nd[k].len);
}
t= nd[k].len+s-cl[k].bound+1;
if(t<=score){
if(t<score||s<best_s||(s==best_s&&nd[k].len> best_l))
score= t,best_itm= k,best_s= s,best_l= nd[k].len,p= 1;
else if(s==best_s&&nd[k].len==best_l){
p++;
if(randomizing&&(mems+= 4,!gb_unif_rand(p)))best_itm= k;
}
}
}
if((vbose&show_details)&&
level<show_choices_max&&level>=maxl-show_choices_gap){
if(score<infty)
fprintf(stderr," branching on "O".8s("O"d)\n",cl[best_itm].name,score);
else fprintf(stderr," solution\n");
}
if(shape_file&&score<infty){
fprintf(shape_file,""O"d "O".8s\n",score>=0?score:0,cl[best_itm].name);
fflush(shape_file);
}
cmems+= mems-tmems;

/*:42*/
#line 644 "dlx3.w"
;
if(score<=0)goto backdown;
if(score==infty)/*43:*/
#line 1049 "dlx3.w"

{
if(shape_file){
fprintf(shape_file,"sol\n");fflush(shape_file);
}
/*44:*/
#line 1057 "dlx3.w"

{
count++;
if(spacing&&(count mod spacing==0)){
printf(""O"lld:\n",count);
for(k= 0;k<level;k++){
pp= choice[k];
cc= pp<last_itm?pp:nd[pp].itm;
if(!first_tweak[k])print_option(pp,stdout,nd[cc].down,scor[k]);
else print_option(pp,stdout,first_tweak[k],scor[k]);
}
fflush(stdout);
}
if(count>=maxcount)goto done;
goto backdown;
}

/*:44*/
#line 1054 "dlx3.w"
;
}

/*:43*/
#line 646 "dlx3.w"
;
scor[level]= score,first_tweak[level]= 0;

oo,cur_node= choice[level]= nd[best_itm].down;
o,cl[best_itm].bound--;
if(cl[best_itm].bound==0&&cl[best_itm].slack==0)cover(best_itm,1);
else{
o,first_tweak[level]= cur_node;
if(cl[best_itm].bound==0)cover(best_itm,1);
}
advance:/*32:*/
#line 727 "dlx3.w"

if((o,cl[best_itm].bound==0)&&(cl[best_itm].slack==0)){
if(cur_node==best_itm)goto backup;
}else if(oo,nd[best_itm].len<=cl[best_itm].bound-cl[best_itm].slack)
goto backup;
else if(cur_node!=best_itm)tweak(cur_node,cl[best_itm].bound);
else if(cl[best_itm].bound!=0){
o,p= cl[best_itm].prev,q= cl[best_itm].next;
oo,cl[p].next= q,cl[q].prev= p;
}

/*:32*/
#line 656 "dlx3.w"
;
if((vbose&show_choices)&&level<show_choices_max)/*30:*/
#line 696 "dlx3.w"

{
fprintf(stderr,"L"O"d:",level);
if(cl[best_itm].bound==0&&cl[best_itm].slack==0)
print_option(cur_node,stderr,nd[best_itm].down,score);
else print_option(cur_node,stderr,first_tweak[level],score);
}

/*:30*/
#line 657 "dlx3.w"
;
if(cur_node> last_itm)
/*36:*/
#line 811 "dlx3.w"

for(pp= cur_node+1;pp!=cur_node;){
o,cc= nd[pp].itm;
if(cc<=0)o,pp= nd[pp].up;
else{
if(cc<second){
oo,cl[cc].bound--;
if(cl[cc].bound==0)cover(cc,1);
}else{
if(!nd[pp].color)cover(cc,1);
else if(nd[pp].color> 0)purify(pp);
}
pp++;
}
}

/*:36*/
#line 659 "dlx3.w"
;
/*29:*/
#line 686 "dlx3.w"

if(++level> maxl){
if(level>=max_level){
fprintf(stderr,"Too many levels!\n");
exit(-4);
}
maxl= level;
}
goto forward;

/*:29*/
#line 660 "dlx3.w"
;
backup:/*33:*/
#line 738 "dlx3.w"

if((o,cl[best_itm].bound==0)&&(cl[best_itm].slack==0))uncover(best_itm,1);
else o,untweak(best_itm,first_tweak[level],cl[best_itm].bound);
oo,cl[best_itm].bound++;

/*:33*/
#line 661 "dlx3.w"
;
backdown:if(level==0)goto done;
level--;
oo,cur_node= choice[level],best_itm= nd[cur_node].itm,score= scor[level];
if(cur_node<last_itm)/*31:*/
#line 704 "dlx3.w"

{
best_itm= cur_node;
o,p= cl[best_itm].prev,q= cl[best_itm].next;
oo,cl[p].next= cl[q].prev= best_itm;
goto backup;
}

/*:31*/
#line 665 "dlx3.w"
;
/*37:*/
#line 830 "dlx3.w"

for(pp= cur_node-1;pp!=cur_node;){
o,cc= nd[pp].itm;
if(cc<=0)o,pp= nd[pp].down;
else{
if(cc<second){
if(o,cl[cc].bound==0)uncover(cc,1);
o,cl[cc].bound++;
}else{
if(!nd[pp].color)uncover(cc,1);
else if(nd[pp].color> 0)unpurify(pp);
}
pp--;
}
}

/*:37*/
#line 666 "dlx3.w"
;
oo,cur_node= choice[level]= nd[cur_node].down;goto advance;

/*:26*/
#line 111 "dlx3.w"
;
done:if(vbose&show_tots)
/*25:*/
#line 603 "dlx3.w"

{
fprintf(stderr,"Item totals:");
for(k= 1;k<last_itm;k++){
if(k==second)fprintf(stderr," |");
fprintf(stderr," "O"d",nd[k].len);
}
fprintf(stderr,"\n");
}

/*:25*/
#line 113 "dlx3.w"
;
if(vbose&show_profile)/*47:*/
#line 1135 "dlx3.w"

{
fprintf(stderr,"Profile:\n");
for(level= 0;level<=maxl;level++)
fprintf(stderr,""O"3d: "O"lld\n",
level,profile[level]);
}

/*:47*/
#line 114 "dlx3.w"
;
if(vbose&show_basics)/*5:*/
#line 218 "dlx3.w"

{
fprintf(stderr,"Altogether "O"llu solution"O"s",
count,count==1?"":"s");
fprintf(stderr,", "O"llu+"O"llu mems,",imems,mems);
fprintf(stderr," "O"llu updates, "O"llu cleansings,",
updates,cleansings);
bytes= last_itm*sizeof(item)+last_node*sizeof(node)+maxl*sizeof(int);
fprintf(stderr," "O"llu bytes, "O"llu nodes,",
bytes,nodes);
fprintf(stderr," ccost "O"lld%%.\n",
(200*cmems+mems)/(2*mems));
}

/*:5*/
#line 115 "dlx3.w"
;
/*6:*/
#line 232 "dlx3.w"

if(shape_file)fclose(shape_file);

/*:6*/
#line 116 "dlx3.w"
;
}

/*:2*/
