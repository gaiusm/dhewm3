#include "sys/platform.h"
#include "renderer/VertexCache.h"
#include "renderer/Cinematic.h"

#include "renderer/tr_local.h"

#include "framework/Common.h"
#include "idlib/MapFile.h"

#define RT_MODULE_CPP
#include "rt_module.h"

const float infinity = 1000.0 * 1000.0 * 1000.0;
const float epsilon  = 0.00001;
const float meter1   = 39.37008;
const float meter2   = meter1 * meter1;


static float sqr (float f)
{
  return f * f;
}


#if 0
static void error (const char *s)
{
  fprintf (stderr, "%s\n", s);
  exit (1);
}
#endif


static rtLight *freeLight = NULL;


rtLight::rtLight ()
{
}


rtLight::~rtLight ()
{
}


rtLight::rtLight (idVec3 pos, float fall, idVec3 col, idVec3 rad)
  : origin(pos), falloff(fall), color(col), radius(rad), next(NULL)
{
}


float rtLight::calcLightLevel (float distance2)
{
  if (distance2 < meter2)
    return 1.0;
  return (1.0 / (meter2 / distance2)) * (1.0 - falloff);
}


rtObject::rtObject ()
  : next(NULL)
{
}


rtObject::~rtObject ()
{
}


static rtObject *freeList = NULL;


rtSphere::rtSphere (idVec3 p, float r, idVec3 sc, idVec3 ec, float tr, float re)
  : pos(p), radius(r), sphereColor(sc), emissionColor(ec),
    transparency(tr), reflection(re)
{
  radius2 = sqr (r);
}


rtSphere::~rtSphere ()
{
}


bool rtSphere::isHit (idVec3 rayorigin, idVec3 raydir,
		      float &distance,
		      float &u, float &v, idVec3 &surfaceNormal, idVec3 &hitPoint)
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
   *  remember the shortest distance to the sphere.
   */
  distance = dproduct - diff;
  hitPoint = rayorigin + raydir * distance;
  surfaceNormal = hitPoint - pos;
  u = 0.0;  /* the texture positions are not used for spheres.  */
  v = 0.0;
  return true;
}


bool rtSphere::isTransparent (float u, float v)
{
  return transparency > epsilon;
}


float rtSphere::getTransparency (float u, float v)
{
  return transparency;
}


/*
 *  rtPolygon - define a polygon using a plane and list of vertices.
 */

rtPolygon::rtPolygon (unsigned int nop, idVec3 *pts,
		      float a, float b, float c, float d)
  : noPoints(nop), A(a), B(b), C(c), D(d)
{
  for (int i = 0; i < nop; i++)
    points[i] = pts[i];
  surfaceNormal = idVec3 {a, b, c};
}


rtPolygon::~rtPolygon ()
{
}


#undef CULLING

/*
 *  isHit - return a boolean indicating whether a ray hits a triangle.
 *          It implements the algorithm presented in the paper:
 *
 *          Fast, Minimum Storage Ray/Triangle Intersection.
 *          Möller and Trumbore. Journal of Graphics Tools, 1997.
 */

bool rtPolygon::isHit (idVec3 rayorigin, idVec3 raydir,
		       float &distance, float &u, float &v,
		       idVec3 &normal, idVec3 &hitPoint)
{
  idVec3 v0v1 = points[1] - points[0];
  idVec3 v0v2 = points[2] - points[0];
  idVec3 pvec = raydir.Cross (v0v2);
  float det = v0v1 * pvec;   /* dot product.  */
#ifdef CULLING
  /*
   *  if the determinant is negative the triangle is backfacing
   *  if the determinant is close to 0, the ray misses the triangle.
   */
  if (det < epsilon)
    return false;
#else
  /*
   *  ray and triangle are parallel if det is close to 0.
   */
  if (fabs (det) < epsilon)
    return false;
#endif
  float invDet = 1 / det;

  idVec3 tvec = rayorigin - points[0];
  u = (tvec * pvec) * invDet;  /* (tvec dotprod pvec) * invDet.  */
  if (u < 0 || u > 1)
    return false;

  idVec3 qvec = tvec.Cross (v0v1);
  v = (raydir * qvec) * invDet;  /* (dir dotprod qvec) * invDet.  */
  if (v < 0 || u + v > 1)
    return false;

  distance = (v0v2 * qvec) * invDet;  /* (v0v2 dotprod qvec) * invDet.  */
  normal = surfaceNormal;
  hitPoint = rayorigin + raydir * distance;
  return true;
}


rtPolygonTexture::rtPolygonTexture (unsigned int nop, idVec3 *pts,
				    float a, float b, float c, float d, idMaterial *mat)
  : rtPolygon (nop, pts, a, b, c, d), material(mat)
{
}


rtPolygonTexture::~rtPolygonTexture ()
{
}


bool rtPolygonTexture::isTransparent (float u, float v)
{
  return false;  // --fixme--  improve this!
}


float rtPolygonTexture::getTransparency (float u, float v)
{
  return 0.0;  // --fixme-- improve this!
}


rtPolygonProcedural::rtPolygonProcedural (unsigned int nop, idVec3 *pts,
					  float a, float b, float c, float d,
					  idVec3 diffuse, idVec3 specular,
					  float transparent, float reflect)
  : rtPolygon (nop, pts, a, b, c, d),
    diffuseColor(diffuse), specularColor(specular),
    transparency(transparent), reflection(reflect)
{
}


rtPolygonProcedural::~rtPolygonProcedural ()
{
}


bool rtPolygonProcedural::isTransparent (float u, float v)
{
  return transparency > epsilon;
}


float rtPolygonProcedural::getTransparency (float u, float v)
{
  return transparency;
}


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


rtLight *rayTraceWorld::newLight (void)
{
  rtLight *obj;

  if (freeLight == NULL)
    obj = (rtLight *) Mem_Alloc (sizeof (rtLight));
  else
    {
      obj = freeLight;
      freeLight = freeLight->next;
    }
  return obj;
}


/*
==============
lightObject - create a light object in the raytracing world.
              The new light is pushed onto the lightArray.
*/

void rayTraceWorld::pushLightObject (idVec3 pos, float fall, idVec3 col, idVec3 rad)
{
  rtLight *obj = newLight ();

  *obj = rtLight (pos, fall, col, rad);
  lightArray[noLight] = obj;
  noLight++;
}


/*
==============
sphereObject - create a procedurally generated sphere object in the raytracing world.
==============
 */

rtObject *rayTraceWorld::sphereObject (idVec3 pos, float radius, idVec3 sphereColor, idVec3 emissionColor, float transparency, float reflection)
{
  rtObject *obj = newObject ();

  *obj = rtSphere (pos, radius, sphereColor, emissionColor, transparency, reflection);
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

  *obj = rtPolygonProcedural (nop, pts, a, b, c, d, diffuse, specular, transparency, reflection);
  return obj;
}


rtObject *rayTraceWorld::polygonObject (unsigned int nop, idVec3 *pts, idVec4 equation,
					idVec3 diffuse, idVec3 specular, float transparency, float reflection)
{
  rtObject *obj = newObject ();

  *obj = rtPolygonProcedural (nop, pts,
			      equation[0], equation[1], equation[2], equation[3],
			      diffuse, specular, transparency, reflection);
  return obj;
}


/*
==============
polygonObject - create a polygon as defined by its vertices and plane equation.
                The polygon uses constant values for its color.
==============
 */

rtObject *rayTraceWorld::polygonObject (unsigned int nop, idVec3 *pts, float a, float b, float c, float d, idMaterial *mat)
{
  rtObject *obj = newObject ();

  *obj = rtPolygonTexture (nop, pts, a, b, c, d, mat);
  return obj;
}


/*
==============
polygonObject - create a polygon as defined by its vertices and plane equation.
                The polygon uses constant values for its color.
==============
 */

rtObject *rayTraceWorld::polygonObject (unsigned int nop, idVec3 *pts, idVec3 equation, idMaterial *mat)
{
  rtObject *obj = newObject ();

  *obj = rtPolygonTexture (nop, pts, equation[0], equation[1], equation[2], equation[3], mat);
  return obj;
}


rayTraceWorld::rayTraceWorld ()
{
  noStatic = 0;
  noDynamic = 0;
  noLight = 0;
}


rayTraceWorld::~rayTraceWorld ()
{
  freeLightObjects ();
  freeDynamicObjects ();
  freeStaticObjects ();
}


void rayTraceWorld::reset (void)
{
  freeLightObjects ();
  freeDynamicObjects ();
  freeStaticObjects ();
}


void rayTraceWorld::freeLightObjects (void)
{
  for (int i = 0; i < noLight; i++)
    {
      lightArray[i]->next = freeLight;
      freeLight = lightArray[i];
      lightArray[i] = NULL;
    }
  noLight = 0;
}


void rayTraceWorld::freeStaticObjects (void)
{
  for (int i = 0; i < noStatic; i++)
    {
      staticArray[i]->next = freeList;
      freeList = staticArray[i];
      staticArray[i] = NULL;
    }
  noStatic = 0;
}


void rayTraceWorld::freeDynamicObjects (void)
{
  for (int i = 0; i < noDynamic; i++)
    {
      dynamicArray[i]->next = freeList;
      freeList = dynamicArray[i];
      dynamicArray[i] = NULL;
    }
  noDynamic = 0;
}


#define MAX_RAY_TRACE_BOUNCES 1

bool rayTraceWorld::RT_ClosestIntersection (idVec3 rayorigin, idVec3 raydir, RT_HitInfo_t *hit)
{
  float distance = infinity;
  rtObject *o = NULL;
  float testDist, u_scale, v_scale;
  idVec3 surfaceNormal, hitPoint;

  /*
   *  check the static objects first.
   */
  for (int i = 0; i < noStatic; i++)
    {
      rtObject *obj = staticArray[i];

      if (obj->isHit (rayorigin, raydir, testDist, u_scale, v_scale, surfaceNormal, hitPoint) && (testDist < distance))
	{
	  distance = testDist;
	  /*
	   *  fill in hit info.
	   */
	  hit->obj = obj;
	  hit->point = hitPoint;
	  hit->surfaceNormal = surfaceNormal;
	  hit->u_scale = u_scale;
	  hit->v_scale = v_scale;
	}
    }
  /*
   *  check the static dynamic objects second.
   */
  for (int i = 0; i < noDynamic; i++)
    {
      rtObject *obj = dynamicArray[i];

      if (obj->isHit (rayorigin, raydir, testDist, u_scale, v_scale, surfaceNormal, hitPoint) && (testDist < distance))
	{
	  distance = testDist;
	  /*
	   *  fill in hit info.
	   */
	  hit->obj = obj;
	  hit->point = hitPoint;
	  hit->surfaceNormal = surfaceNormal;
	  hit->u_scale = u_scale;
	  hit->v_scale = v_scale;
	}
    }
  if (o == NULL)
    return false;
  return true;
}


/*
==================
RT_Trace

return the ray color as defined by its origin and direction.  RT_Trace tests whether
the ray intersects with an object (model or map).  If there is an intersection then
the point of intersection is calculated (the normal).  The point of intersection
is used to color the ray (it will use diffuse and specular information).
If nothing is hit it returns black.
==================
 */

idVec3 rayTraceWorld::RT_Trace (idVec3 rayorigin, idVec3 raydir, unsigned int depth)
{
  /* the color of the ray or surface of the object which is intersected by the ray.  */
  RT_HitInfo_t hit;

  if (RT_ClosestIntersection (rayorigin, raydir, &hit))
    return RT_Shade (rayorigin, raydir, &hit, depth);
  /*
   *  no hit.
   */
  idVec3 surface_color;
  surface_color.Zero ();  // default to black
  return surface_color;
}


/*
==============
RT_Bounce - if the surface is reflective or transparent then bounce the
            ray and change color accordingly.
==============
 */

idVec3 rayTraceWorld::RT_Bounce (idVec3 rayorigin, idVec3 raydir,
				 RT_HitInfo_t *hit, idVec3 color, unsigned int depth)
{
  if (depth < MAX_RAY_TRACE_BOUNCES)
    {
      /*
       *  we have not reached the limit of raytracing.
       */
      if (hit->reflective > 0)
	color = RT_Reflective (rayorigin, raydir, hit, color, depth + 1);

      if (hit->transparent > 0)
	color = RT_Transparent (rayorigin, raydir, hit, color, depth + 1);
    }
  return color;
}


float blend (float a, float b, float proportion)
{
  return a * (1.0 - proportion) + b * proportion;
}


idVec3 blendColor (idVec3 a, idVec3 b, float proportion)
{
  return a * (1.0 - proportion) + b * proportion;
}


/*
 *  RT_Reflective - continue to trace the ray though a surface reflection.
 */

idVec3 rayTraceWorld::RT_Reflective (idVec3 rayorigin, idVec3 raydir,
				     RT_HitInfo_t *hit, idVec3 color, unsigned int depth)
{
  float dotProd = raydir * hit->surfaceNormal;
  idVec3 reflectedDir = raydir - (hit->surfaceNormal * 2 * dotProd);
  reflectedDir.Normalize ();
  idVec3 reflectedColor = RT_Trace (hit->point, reflectedDir, depth);
  return blendColor (color, reflectedColor, hit->reflective);
}


idVec3 rayTraceWorld::RT_Transparent (idVec3 rayorigin, idVec3 raydir,
				      RT_HitInfo_t *hit, idVec3 color, unsigned int depth)
{
  float dotProd = raydir * hit->surfaceNormal;
  idVec3 reflectedDir = raydir - (hit->surfaceNormal * 2 * dotProd);
  reflectedDir.Normalize ();
  idVec3 transparentColor = RT_Trace (hit->point, reflectedDir, depth);
  return blendColor (color, transparentColor, hit->transparent);
}


/*
==================
RT_Shade - return the pixel value given the hit location, rayorigin and raydir.  (gaius)
           If depth reaches MAX_RAY_TRACE_BOUNCES then black is returned.
==================
 */

idVec3 rayTraceWorld::RT_Shade (idVec3 rayorigin, idVec3 raydir,
				RT_HitInfo_t *hit, unsigned int depth)
{
  idVec3 color;

  color = RT_Lights (hit);
  color = RT_Bounce (rayorigin, raydir, hit, color, depth);
  return color;
}


/*
 *  Rt_BlendTextureLight - given a surface, color, blend the lightColor into the
 *                         surface color and return the result.
 */

idVec3 rayTraceWorld::RT_BlendTextureLight (idVec3 color, RT_HitInfo_t *hit, idVec3 lightColor)
{
  return blendColor (color, lightColor, hit->transparent + hit->reflective);
}


/*
 *  RT_LightLineSight - returns true if any light directly hits toPoint from light.
 *                      The color parameter is changed to the color of the light
 *                      falling on toPoint.  The light->color might be affected
 *                      by the falloff of the light and passing though transparent
 *                      surfaces.
 */

bool rayTraceWorld::RT_LightLineSight (rtLight *light, idVec3 toPoint, idVec3 *color)
{
  idVec3 col = light->color;
  idVec3 dir = toPoint - light->origin;
  float distance2 = dir.LengthSqr ();
  float t, u, v;
  idVec3 normal, hitPoint;
  dir.Normalize ();

  for (int i = 0; i < noStatic; i++)
    {
      rtObject *obj = staticArray[i];

      if (obj->isHit (light->origin, dir, t, u, v, normal, hitPoint) && (t * t < distance2))
	{
	  if (! obj->isTransparent (u, v))
	    return false;
	  col = col * obj->getTransparency (u, v) * light->calcLightLevel (distance2);
	}
    }
  for (int i = 0; i < noDynamic; i++)
    {
      rtObject *obj = dynamicArray[i];

      if (obj->isHit (light->origin, dir, t, u, v, normal, hitPoint) && (t * t < distance2))
	{
	  if (! obj->isTransparent (u, v))
	    return false;
	  col = col * obj->getTransparency (u, v) * light->calcLightLevel (distance2);
	}
    }
  *color = col;
  return true;
}


/*
===============
RT_Lights - for each light which is directly in line of sight to hit
            blend the light color with the texture at hit and return
            this overall color.  This computes the primary pixel color.
===============
 */

idVec3 rayTraceWorld::RT_Lights (RT_HitInfo_t *hit)
{
  idVec3 blendedColor = hit->diffuse;
  idVec3 color;

  color.Zero ();   /* no light will generate a black pixel.  */
  for (int i = 0; i < noLight; i++)
    {
      rtLight *l = lightArray[i];
      idVec3 ray2light = l->origin - hit->point;
      if (hit->surfaceNormal * ray2light > 0)  /* dot product > 0.  */
	{
	  /*
	   *  now we need to check the light is not in shadow.
	   *  Ie it has a direct line of sight with the hit->point.
	   */
	  idVec3 lightColor;

	  if (RT_LightLineSight (l, hit->point, &lightColor))
	    {
	      /*
	       *  blend the amount of light hitting the texture
	       */
	      blendedColor = RT_BlendTextureLight (blendedColor, hit, lightColor);
	    }
	}
    }
  return color + blendedColor;
}


/*
================
traceRays - generate a ray traced image in buffer of the world as seen by ref (gaius).
            Working title the SPF (Seconds/Frame) Mod.
================
*/

void rayTraceWorld::traceRays (byte *buffer, renderView_t *ref)
{
  float invWidth = 1.0 / float (ref->width);
  float invHeight = 1.0 / float (ref->height);
  float aspectratio = ref->width / float (ref->height);
  float angle_x = tan (M_PI * 0.5 * ref->fov_x / 180.0);
  float angle_y = tan (M_PI * 0.5 * ref->fov_y / 180.0);
  int count = 0;
  idVec3 pixel;

  for (unsigned j = 0; j < ref->height; j++)
    {
      for (unsigned i = 0; i < ref->width; i++)
	{
	  float x = (2 * ((i + 0.5) * invWidth) - 1) * angle_x * aspectratio;
	  float y = (1 - 2 * ((j + 0.5) * invHeight)) * angle_y;
	  idVec3 raydir (x, y, -1);    /* -1 must be wrong - fixme sometime.  (ref->viewaxis ?).  */
	  idVec3 rayorigin = ref->vieworg;

	  raydir.Normalize ();
	  pixel = RT_Trace (rayorigin, raydir, 0);
	  /*
	   *  add pixel into the buffer.
	   */
	  for (unsigned k = 0; k < 3; k++)
	    {
	      buffer[count] = byte (pixel[k] * 255);
	      count++;
	    }
	}
    }
}


void rayTraceWorld::PushBrushSide (idMapBrushSide *s)
{
  const idPlane p = s->GetPlane ();
  idVec3 mat1, mat2;
  s->GetTextureMatrix (mat1, mat2);
  idVec4 equation = p.ToVec4 ();
#if 0
  pushStatic (polygonObject (,
			     equation,
			     declManager->FindMaterial (s->GetMaterial ())));
#endif
}


void rayTraceWorld::DiscoverBrushPolygons (idPlane *planes, idMapBrush *b)
{
  idVec3 points[MAX_RT_POINTS];
  int nPoints = 0;

#if 0
  for (int i = 0; i < b->GetNumSides (); i++)
    for (int j = 0; j < b->GetNumSides (); j++)
      for (int k = 0; k < b->GetNumSides (); k++)
	{
	  if ( )
	}
#endif

}



void rayTraceWorld::LoadBrush (idMapBrush *b)
{
  int i, j;
  idMapBrushSide *mapSide;
  idFixedWinding w;
  idPlane *planes;
  const idMaterial *material;

  /* fix degenerate planes.  */
  planes = (idPlane *) alloca (b->GetNumSides () * sizeof (planes[0]));
  for (i = 0; i < b->GetNumSides (); i++)
    {
      planes[i] = b->GetSide (i)->GetPlane ();
      planes[i].FixDegeneracies (DEGENERATE_DIST_EPSILON);
    }

  DiscoverBrushPolygons (planes, b);
}


#if 0
  for (i =
  /* create a collision polygon for each brush side.  */
  for (i = 0; i < b->GetNumSides (); i++)
    {
      mapSide = b->GetSide (i);
      material = declManager->FindMaterial (mapSide->GetMaterial ());
      if ((material->GetContentFlags () & CONTENTS_REMOVE_UTIL) != 0)
	{
	  w.BaseForPlane (-planes[i]);
	  for (j = 0; j < b->GetNumSides () && w.GetNumPoints(); j++)
	    {
	      if (i != j)
		w.ClipInPlace (-planes[j], 0);
#if 0
	      if (w.GetNumPoints ())
		LoadPolygonFromWinding (&w, planes[i], material);
#endif
	    }
	}
    }
}
#endif


void rayTraceWorld::LoadPrimitive (idMapPrimitive *p)
{
  switch (p->GetType ())
    {
    case idMapPrimitive::TYPE_BRUSH:
      LoadBrush (static_cast<idMapBrush*>(p));
      break;
    case idMapPrimitive::TYPE_PATCH:
      // static_cast<idMapPatch*>(mapPrim)->Write( fp, i, origin );  // --fixme-- (gaius)
      break;
    }
}


void rayTraceWorld::addDefaultObjects (void)
{
  const idVec3 silver = idVec3 (192.0, 192.0, 192.0);
  /*
   *   moon light!
   */
  pushLightObject (idVec3 (0.0, 0.0, 100000.0), 0.0, silver, idVec3 (255.0, 255.0, 255.0));
}


void rayTraceWorld::LoadMap (idMapFile *mapFile)
{
  reset ();  /* empty the current world of any objects.  */
  addDefaultObjects ();
  for (int i = 0; i < mapFile->GetNumEntities(); i++)
    {
      idMapEntity *mapEnt = mapFile->GetEntity (i);
      for (int j = 0; j < mapEnt->GetNumPrimitives (); j++)
	{
	  idMapPrimitive *p = mapEnt->GetPrimitive (j);
	  LoadPrimitive (p);
	}
    }
}


void rt_module_init (void)
{
  if (rt_world == NULL)
    rt_world = new rayTraceWorld;
  else
    rt_world->reset ();
}


void rt_module_finish (void)
{
  rt_world->reset ();
}
