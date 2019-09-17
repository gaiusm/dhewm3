/* do not edit - -moved into ../game.  */

#include "sys/platform.h"
#include "renderer/VertexCache.h"
#include "renderer/Cinematic.h"

#include "renderer/tr_local.h"

#include "framework/Common.h"


#define MAX_RT_POINTS 10


static float sqr (float f)
{
  return f * f;
}


static void error (const char *s)
{
  fprintf (stderr, "%s\n", s);
  exit (1);
}


class rtObject {
public:
  rtObject ();
  ~rtObject ();
  bool isHit (idVec3 rayorigin, idVec3 raydir, float &distance);
  rtObject *next;   /* free list of objects.  */
};


rtObject::rtObject ()
  : next(NULL)
{
}


rtObject::~rtObject ()
{
}


static rtObject *freeList = NULL;


class rtSphere: public rtObject {
public:
  rtSphere ();
  ~rtSphere ();
  rtSphere (idVec3 pos, float radius, idVec3 sphereColour, idVec3 emissionColour, float transparency, float reflection);
  bool isHit (idVec3 rayorigin, idVec3 raydir, float &distance);
private:
  idVec3 pos;
  float radius;
  float radius2;
  idVec3 sphereColour;
  idVec3 emissionColour;
  float transparency;
  float reflection;
};


rtSphere::rtSphere (idVec3 p, float r, idVec3 sc, idVec3 ec, float tr, float re)
  : pos(p), radius(r), sphereColour(sc), emissionColour(ec),
    transparency(tr), reflection(re)
{
  radius2 = sqr (r);
}


rtSphere::~rtSphere ()
{
}


bool rtSphere::isHit (idVec3 rayorigin, idVec3 raydir, float &distance)
{
  idVec3 ray2sphere = pos - rayorigin;
  float dproduct = ray2sphere * raydir;
  if (dproduct < 0)
    /*
     *  ray misses sphere.
     */
    return false;
  float determinant2 = ray2sphere * ray2sphere - sqr (dproduct);
  if (determinant2 > radius2)
    return false;
  float diff = sqrt (radius2 - determinant2);
  /*
   *  only interested in the shortest distance to the sphere.
   */
  distance = dproduct - diff;
  return true;
}


class rtPolygon: public rtObject {
public:
  rtPolygon ();
  ~rtPolygon ();
  rtPolygon (unsigned int nop, idVec3 *pts, float a, float b, float c, float d, idMaterial *mat);
  rtPolygon (unsigned int nop, idVec3 *pts, float a, float b, float c, float d,
	     idVec3 diffuse, idVec3 specular, float transparency, float reflection);
  bool isHit (idVec3 rayorigin, idVec3 raydir, float &distance);
private:
  unsigned int noPoints;
  idVec3 points[MAX_RT_POINTS];
  float A;
  float B;
  float C;
  float D;
  idMaterial *material;
  idVec3 diffuseColour;  /* if material is NULL then these values will be used.  */
  idVec3 specularColour;
  float transparency;
  float reflection;
};


rtPolygon::rtPolygon (unsigned int nop, idVec3 *pts,
		      float a, float b, float c, float d, idMaterial *mat)
  : noPoints(nop), A(a), B(b), C(c), D(d), material(mat)
{
  for (int i = 0; i < nop; i++)
    points[i] = pts[i];

  diffuseColour.Zero ();
  specularColour.Zero ();
  transparency = 0;
  reflection = 0;
}


rtPolygon::rtPolygon (unsigned int nop, idVec3 *pts,
		      float a, float b, float c, float d,
		      idVec3 diffuse, idVec3 specular, float transparent, float reflect)
  : noPoints(nop), A(a), B(b), C(c), D(d), material(NULL),
    diffuseColour(diffuse), specularColour(specular),
    transparency(transparent), reflection(reflect)
{
  for (int i = 0; i < nop; i++)
    points[i] = pts[i];
}


rtPolygon::~rtPolygon ()
{
}


bool isHit (idVec3 rayorigin, idVec3 raydir, float &distance)
{

}


class rayTraceWorld {
public:
  rayTraceWorld ();
  ~rayTraceWorld ();  // destructor

  rayTraceWorld (const rayTraceWorld &from);              // copy
  rayTraceWorld& operator= (const rayTraceWorld &from);   // assignment

  void pushStatic (rtObject *o);
  void pushDynamic (rtObject *o);
  void freeDynamicObjects (void);

  rtObject& operator[] (int idx);
  const rtObject& operator[] (int idx) const;

  void freeObject (unsigned int i);
  unsigned int noObjects (void);
  unsigned int noStaticObjects (void);
  unsigned int noDynamicObjects (void);
  rtObject *newObject (void);

  rtObject *sphereObject (idVec3 pos, float radius, idVec3 sphereColour, idVec3 emissionColour, float transparency, float reflection);
  rtObject *polygonObject (unsigned int nop, idVec3 *pts, float a, float b, float c, float d, idMaterial *mat);
  rtObject *polygonObject (unsigned int nop, idVec3 *pts,  float a, float b, float c, float d, idVec3 diffuse, idVec3 specular, float transparency, float reflection);
private:
  unsigned int noDynamic;
  unsigned int noStatic;
  rtObject *dynamicArray;
  rtObject *staticArray;
};


rtObject *rayTraceWorld::newObject (void)
{
  rtObject *obj;

  if (freeList == NULL)
    obj = (rtObject *) Mem_Alloc (sizeof (rtObject));
  else
    {
      obj = freeList;
      freeList = freeList->next;
    }
  return obj;
}


/*
==============
sphereObject - create a procedurally generated sphere object in the raytracing world.
==============
 */

rtObject *rayTraceWorld::sphereObject (idVec3 pos, float radius, idVec3 sphereColour, idVec3 emissionColour, float transparency, float reflection)
{
  rtObject *obj = newObject ();

  *obj = rtSphere (pos, radius, sphereColour, emissionColour, transparency, reflection);
  return obj;
}


/*
==============
polygonObject - create a polygon as defined by its vertices and plane equation.
                The polygon uses the idMaterial for textures.
                --fixme-- transformation matrix is required.
==============
 */

rtObject *rayTraceWorld::polygonObject (unsigned int nop, idVec3 *pts, float a, float b, float c, float d,
					idVec3 diffuse, idVec3 specular, float transparency, float reflection)
{
  rtObject *obj = newObject ();

  *obj = rtPolygon (nop, pts, a, b, c, d, diffuse, specular, transparency, reflection);
  return obj;
}


/*
==============
polygonObject - create a polygon as defined by its vertices and plane equation.
                The polygon uses constant values for its colour.
==============
 */

rtObject *rayTraceWorld::polygonObject (unsigned int nop, idVec3 *pts, float a, float b, float c, float d, idMaterial *mat)
{
  rtObject *obj = newObject ();

  *obj = rtPolygon (nop, pts, a, b, c, d, mat);
  return obj;
}


/*
 *  overload [] for non-const and also assignment.
 */

rtObject& rayTraceWorld::operator[](int idx)
{
  if (idx < noStatic)
    return staticArray[idx];
  if (idx < noStatic + noDynamic)
    return dynamicArray[idx-noStatic];
  error (__FILE__ ":array index out of bounds");
  return staticArray[0];
}


/*
 *  overload [] for read access to the array.
 */

const rtObject& rayTraceWorld::operator[](int idx) const
{
  if (idx < noStatic)
    return staticArray[idx];
  if (idx < noStatic + noDynamic)
    return dynamicArray[idx-noStatic];
  error (__FILE__ ":array index out of bounds");
  return staticArray[0];
}


rayTraceWorld::rayTraceWorld ()
{
  dynamicArray = NULL;
  staticArray = NULL;
  noStatic = 0;
  noDynamic = 0;
}
