#if defined(RT_MODULE_CPP)
#define EXTERN
#else
#define EXTERN extern
#endif


#define MAX_RT_POINTS             10
#define MAX_RT_LIGHTS           1000
#define MAX_RT_DYNAMIC_OBJECTS  2000
#define MAX_RT_STATIC_OBJECTS  10000


typedef struct rt_trace_s {
  idVec3 surfaceColor;
  idVec3 reflection;
  idVec3 refraction;
} rt_trace_t;


class rtLight {
public:
  rtLight ();
  ~rtLight ();  // destructor

  rtLight (idVec3 pos, float fall, idVec3 col, idVec3 rad);
  float calcLightLevel (float distance2);
  idVec3 origin;
  float falloff;
  idVec3 color;
  idVec3 radius;
  rtLight *next;
};


class rtObject {
public:
  rtObject ();
  ~rtObject ();
  virtual bool isHit (idVec3 rayorigin, idVec3 raydir, float &distance, float &u, float &v, idVec3 &surfaceNormal, idVec3 &hitPoint) =0;
  virtual bool isTransparent (float u, float v) =0;
  virtual float getTransparency (float u, float v) =0;
  rtObject *next;   /* free list of objects.  */
};


typedef struct RT_HitInfo_s {
  idVec3 point;  /* which real world position was hit?  */
  idVec3 surfaceNormal;
  float reflective;
  float transparent;
  idVec3 diffuse;   /* the color of the texture at the hit point.  */
  rtObject *obj;  /* which object was hit?  */
  float u_scale;  /* where on the polygon did the hit occur.  */
  float v_scale;
} RT_HitInfo_t;


class rtSphere: public rtObject {
public:
  rtSphere ();
  ~rtSphere ();
  rtSphere (idVec3 pos, float radius, idVec3 sphereColor, idVec3 emissionColor, float transparency, float reflection);
  bool isHit (idVec3 rayorigin, idVec3 raydir, float &distance, float &u, float &v, idVec3 &surfaceNormal, idVec3 &hitPoint);
  bool isTransparent (float u, float v);
  float getTransparency (float u, float v);
private:
  idVec3 pos;
  float radius;
  float radius2;
  idVec3 sphereColor;
  idVec3 emissionColor;
  float transparency;
  float reflection;
};


class rtPolygon: public rtObject {
public:
  rtPolygon ();
  ~rtPolygon ();
  rtPolygon (unsigned int nop, idVec3 *pts, float a, float b, float c, float d);
  bool isHit (idVec3 rayorigin, idVec3 raydir, float &distance, float &u, float &v, idVec3 &normal, idVec3 &hitPoint);
  virtual bool isTransparent (float u, float v)  =0;
  virtual float getTransparency (float u, float v) =0;
private:
  unsigned int noPoints;
  idVec3 points[MAX_RT_POINTS];
  float A;
  float B;
  float C;
  float D;
  idVec3 surfaceNormal;
};


class rtPolygonTexture: public rtPolygon {
public:
  rtPolygonTexture ();
  ~rtPolygonTexture ();
  rtPolygonTexture (unsigned int nop, idVec3 *pts,
		    float a, float b, float c, float d, idMaterial *mat);
  bool isTransparent (float u, float v);
  float getTransparency (float u, float v);
private:
  idMaterial *material;
};


class rtPolygonProcedural: public rtPolygon {
public:
  rtPolygonProcedural (unsigned int nop, idVec3 *pts, float a, float b, float c, float d,
		       idVec3 diffuse, idVec3 specular, float transparent, float reflect);
  ~rtPolygonProcedural ();
  bool isTransparent (float u, float v);
  float getTransparency (float u, float v);
private:
  idVec3 diffuseColor;
  idVec3 specularColor;
  float transparency;
  float reflection;
};


class rayTraceWorld {
public:
  rayTraceWorld ();
  ~rayTraceWorld ();  // destructor

  rayTraceWorld (const rayTraceWorld &from);              // copy
  rayTraceWorld& operator= (const rayTraceWorld &from);   // assignment

  void reset (void);
  void pushStatic (rtObject *o);
  void pushDynamic (rtObject *o);
  void freeDynamicObjects (void);
  void freeStaticObjects (void);
  void freeLightObjects (void);
  void pushLightObject (idVec3 pos, float fall, idVec3 col, idVec3 rad);

  void freeObject (unsigned int i);
  unsigned int noObjects (void);
  unsigned int noStaticObjects (void);
  unsigned int noDynamicObjects (void);
  rtObject *newObject (void);
  rtLight *newLight (void);

  rtObject *sphereObject (idVec3 pos, float radius, idVec3 sphereColor, idVec3 emissionColor, float transparency, float reflection);
  rtObject *polygonObject (unsigned int nop, idVec3 *pts, float a, float b, float c, float d, idMaterial *mat);
  rtObject *polygonObject (unsigned int nop, idVec3 *pts,  float a, float b, float c, float d, idVec3 diffuse, idVec3 specular, float transparency, float reflection);
  rtObject *polygonObject (unsigned int nop, idVec3 *pts, idVec4 equation, idVec3 diffuse, idVec3 specular, float transparency, float reflection);
  rtObject *polygonObject (unsigned int nop, idVec3 *pts, idVec3 equation, idMaterial *mat);

  idVec3 RT_Lights (RT_HitInfo_t *hit);
  bool RT_LightLineSight (rtLight *light, idVec3 toPoint, idVec3 *color);
  idVec3 RT_BlendTextureLight (idVec3 color, RT_HitInfo_t *hit, idVec3 lightColor);
  bool RT_ClosestIntersection (idVec3 rayorigin, idVec3 raydir, RT_HitInfo_t *hit);
  idVec3 RT_Trace (idVec3 rayorigin, idVec3 raydir, unsigned int depth);
  idVec3 RT_Shade (idVec3 rayorigin, idVec3 raydir, RT_HitInfo_t *hit, unsigned int depth);
  idVec3 RT_Bounce (idVec3 rayorigin, idVec3 raydir, RT_HitInfo_t *hit, idVec3 color, unsigned int depth);
  idVec3 RT_Reflective (idVec3 rayorigin, idVec3 raydir, RT_HitInfo_t *hit, idVec3 color, unsigned int depth);
  idVec3 RT_Transparent (idVec3 rayorigin, idVec3 raydir, RT_HitInfo_t *hit, idVec3 color, unsigned int depth);
  void traceRays (byte *buffer, renderView_t *ref);
  void LoadMap (idMapFile *mapFile);
  void LoadPrimitive (idMapPrimitive *p);
  void LoadBrush (idMapBrush *b);
  void PushBrushSide (idMapBrushSide *s);
  void addDefaultObjects (void);
  void DiscoverBrushPolygons (idPlane *planes, idMapBrush *b);

private:
  unsigned int noDynamic;
  unsigned int noStatic;
  unsigned int noLight;
  rtObject *dynamicArray[MAX_RT_DYNAMIC_OBJECTS];
  rtObject *staticArray[MAX_RT_STATIC_OBJECTS];
  rtLight *lightArray[MAX_RT_LIGHTS];
};


EXTERN rayTraceWorld *rt_world;
EXTERN void rt_module_init (void);
EXTERN void rt_module_finish (void);

#undef EXTERN
