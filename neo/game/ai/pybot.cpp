/*
===========================================================================

Doom 3 GPL Source Code
Copyright (C) 2017 Free Software Foundation.

This file is part of the Doom 3 GPL Source Code ("Doom 3 Source Code").

Doom 3 Source Code is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Doom 3 Source Code is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Doom 3 Source Code.  If not, see <http://www.gnu.org/licenses/>.

In addition, the Doom 3 Source Code is also subject to certain additional terms. You should have received a copy of these additional terms immediately following the terms and conditions of the GNU General Public License which accompanied the Doom 3 Source Code.  If not, please request a copy in writing from id Software at the address below.

If you have questions concerning this license or the applicable additional terms, you may contact in writing id Software LLC, c/o ZeniMax Media Inc., Suite 120, Rockville, Maryland 20850 USA.

===========================================================================

Author:  Gaius Mulley  <gaius.mulley@southwales.ac.uk>
*/

#define PYBOT_C
#include "pybot.h"

#  include <sys/socket.h>
#  include <netinet/in.h>
#  include <unistd.h>
#  include <limits.h>

#include "sys/platform.h"
#include "idlib/LangDict.h"
#include "idlib/Timer.h"
#include "idlib/Str.h"

#include "framework/async/NetworkSystem.h"
#include "framework/BuildVersion.h"
#include "framework/DeclEntityDef.h"
#include "framework/FileSystem.h"
#include "renderer/ModelManager.h"

#include "gamesys/SysCvar.h"
#include "gamesys/SysCmds.h"
#include "script/Script_Thread.h"

#include "ai/AI.h"
#include "anim/Anim_Testmodel.h"
#include "Camera.h"
#include "SmokeParticles.h"
#include "Player.h"
#include "WorldSpawn.h"
#include "Misc.h"
#include "Trigger.h"
#include "Game_local.h"

const bool debugging = false;
const bool protocol_debugging = false;

#define S(x) #x
#define S_(x) S(x)
#define S__LINE__ S_(__LINE__)
# define pybot_debugf(X)  do { debugf (__FILE__ ":" S__LINE__ ":" ":" X) ; } while (0)
#define MAX_ID_STR  20

int define (const char *name, idAI *idBot, int instance);
int checkId (int id);
void initialise_dictionary (void);


void debugf (const char *s)
{
  if (debugging)
    gameLocal.Printf (s);
}

static void localExit (int code)
{
  gameLocal.Printf (__FILE__ ": exiting with code %d\n", code);
  exit (code);
}

#define MAX_PY_SERVERS 1000
#define MAX_PYLIST MAX_PY_SERVERS
#define ERROR(X)  do { pybot_debugf ("internal error: " X "\n"); localExit (1); } while (0)

static int superServerPort = 7000;

static pyServerClass *super = NULL;
static unsigned int maxId = 0;


char *getHome (void)
{
  return getenv ("HOME");
}


const char *getDir (void)
{
  return ".local/share/dhewm3/base/maps";
}


#define MAX_NAME 100


class item
{
 public:
  item (void);
  ~item (void);
  item (const item &from);
  item (const char *n, idAI *idBot, int id);
  item (const char *n, idPlayer *ip, int id);
  idVec3 getPos (void);
  bool stepDirection (float dir);
  int stepForward (int vel, int dist);
  int stepRight (int vel, int dist);
  int stepVec (int velforward, int velright, int dist);
  int start_firing (void);
  int stop_firing (void);
  int ammo (int weapon_number);
  int stepUp (int vel, int dist);
  int weapon (int new_weapon);
  int health (void);
  int angle (void);
  int reload_weapon (void);
  bool aim (idEntity *enemy);
  int turn (int angle, int angle_vel);
  idEntity *getIdEntity (void);
  void select (int mask);
  int getInstanceId (void);
  const char *getName (void);
  bool canSeeEntity (int entNo);
  idVec4 visibility (idVec4 value);
  idVec4 visibilityParameters (idVec4 value);
  bool visibilityFlag (bool value);
  void getSelfEntityNames (char *buffer, int length);
  int setVisibilityShader (char *buffer);
  int flipVisibility (void);
  int changeWeapon (int weapon_number);
  int inventoryWeapon (int new_weapon);
  int dropWeapon (void);

 private:
  enum {item_none, item_monster, item_player, item_ammo} kind;
  idAI *idai;
  idPlayer *idplayer;
  char name[MAX_NAME];
  int instanceId;
};


item::item (void)
  : kind (item_none), idai (NULL)
{
  instanceId = -1;
}


item::~item (void)
{
}


item::item (const item &from)
{
  *this = from;
}


/*
 *  n is the name.
 *  idBot is the idtech4 bot object.
 *  id is the python instance number.
 */

item::item (const char *n, idAI *idBot, int id)
{
  kind = item_monster;
  strcpy (name, n);
  idai = idBot;
  instanceId = id;
}


item::item (const char *n, idPlayer *ip, int id)
{
  kind = item_player;
  strcpy (name, n);
  idplayer = ip;
  instanceId = id;
}


int item::getInstanceId (void)
{
  return instanceId;
}


const char *item::getName (void)
{
  return &name[0];
}

/*
 *  getPos - return the position of the item.
 */

idVec3 item::getPos (void)
{
  switch (kind)
    {
    case item_monster:
      return idai->GetPos ();
    case item_player:
      return idplayer->GetPos ();
    }
  ERROR ("case needs finishing");
  idVec3 value;

  value.Zero ();
  return value;
}


/*
 *  stepDirection - step forward in direction, dir.
 */

bool item::stepDirection (float dir)
{
  switch (kind)
    {
    case item_monster:
      return idai->StepDirection (dir);
#if 0
    case item_player:
      return idplayer->StepDirection (dir);
#endif
    }
  return false;
}


/*
 *  stepRight - step forward, units.
 */

int item::stepRight (int vel, int dist)
{
  switch (kind)
    {
#if 0
    case item_monster:
      return idai->StepDirection (vel, dist);
#endif
    case item_player:
      return idplayer->setRight (vel, dist);
    }
  return 0;
}


/*
 *  stepForward - step forward at velocity, vel, and over distance, dist.
 */

int item::stepForward (int vel, int dist)
{
  switch (kind)
    {
#if 0
    case item_monster:
      return idai->StepDirection (vel, dist);
#endif
    case item_player:
      return idplayer->setForward (vel, dist);
    }
  return 0;
}


/*
 *  stepForward - step forward at velocity, vel, and over distance, dist.
 */

int item::stepVec (int velforward, int velright, int dist)
{
  switch (kind)
    {
#if 0
    case item_monster:
      return idai->StepDirection (vel, dist);
#endif
    case item_player:
      return idplayer->setVec (velforward, velright, dist);
    }
  return 0;
}


/*
 *  aim - aim our weapon at enemy.
 *        True is returned if the enemy is visible.
 *        False is returned if the enemy is not visible.
 */

bool item::aim (idEntity *enemy)
{
  switch (kind)
    {
#if 0
    case item_monster:
      return idai->Aim (enemy);   // --fixme-- is this correct?
#endif
    case item_player:
      return idplayer->Aim (enemy);
    }
 return false;
}


/*
 *  turn - turn bot to angle at speed, angle_vel.
 *         The current angle of the bot is returned.
 */

int item::turn (int angle, int angle_vel)
{
  switch (kind)
    {
#if 0
    case item_monster:
      return idai->Turn (angle, angle_vel);
#endif
    case item_player:
      return idplayer->Turn (angle, angle_vel);
    }
  assert (false);
  return 0;
}


/*
 *  changeWeapon - attempt to select weapon, new_weapon.
 *                 If successful return the amount of ammo else return -1.
 */

int item::changeWeapon (int new_weapon)
{
  switch (kind)
    {
    case item_player:
      return idplayer->ChangeWeapon (new_weapon);
    }
  assert (false);
  return 0;
}


/*
 *  inventoryWeapon - return 1 if the new_weapon is available for use by the bot.
 *                    return 0 if the bot does not have new_weapon in its inventory.
 */

int item::inventoryWeapon (int new_weapon)
{
  switch (kind)
    {
    case item_player:
      return idplayer->InventoryWeapon (new_weapon);
    }
  assert (false);
  return 0;
}


/*
 *  dropWeapon - return 1 if the current weapon was dropped.
 *               return 0 if the bot does not have new_weapon in its inventory.
 */

int item::dropWeapon (void)
{
  switch (kind)
    {
    case item_player:
      if (idplayer->BotDropWeapon ())
	return 1;
      return 0;
    }
  assert (false);
  return 0;
}


/*
 *  start_firing - start firing and return the amount of ammo.
 */

int item::start_firing (void)
{
  switch (kind)
    {
#if 0
    case item_monster:
      return idai->StartFire ();  // --fixme-- is this correct?
#endif
    case item_player:
      return idplayer->Fire (true);
    }
  assert (false);
  return 0;
}


/*
 *  stop_firing - stop firing and return the amount of ammo.
 */

int item::stop_firing (void)
{
  switch (kind)
    {
#if 0
    case item_monster:
      return idai->StopFire ();  // --fixme-- is this correct?
#endif
    case item_player:
      return idplayer->Fire (false);
    }
  assert (false);
  return 0;
}


/*
 *  ammo - return the amount of ammo left for weapon_number.
 */

int item::ammo (int weapon_number)
{
  switch (kind)
    {
    case item_monster:
      return 0;  // do monsters reload?
      break;
    case item_player:
      return idplayer->InventoryAmmo (weapon_number);
    }
  assert (false);
  return 0;
}


/*
 *  make this bot perform a step up at speed, vel, over a distance, dist.
 *  A negative vel is a crouch.
 */

int item::stepUp (int vel, int dist)
{
  switch (kind)
    {
#if 0
    case item_monster:
      return idai->stepUp (vel, dist);
#endif
    case item_player:
      return idplayer->stepUp (vel, dist);
    }
  assert (false);
  return 0;
}


/*
 *  health -
 */

int item::health (void)
{
  switch (kind)
    {
    case item_monster:
      assert (false);
      return 0;  // ignore
      break;
    case item_player:
      return idplayer->health;
    }
  assert (false);
  return 0;
}


/*
 *  angle -
 */

int item::angle (void)
{
  switch (kind)
    {
    case item_monster:
      assert (false);
      return 0;  // ignore
      break;
    case item_player:
      return idplayer->GetYaw ();
    }
  assert (false);
  return 0;
}


bool item::canSeeEntity (int entNo)
{
  switch (kind)
    {
    case item_monster:
      assert (false);
      return false;   // not finished
      break;
    case item_player:
      return idplayer->isVisible (entNo);
    }
  assert (false);
  return false;
}


/*
 *  reload_weapon
 */

int item::reload_weapon (void)
{
  switch (kind)
    {
    case item_monster:
      return 0;  // do monsters reload?
      break;
    case item_player:
      idplayer->Reload ();
      return idplayer->Ammo ();
    }
  assert (false);
  return 0;
}


/*
 *  select
 */

void item::select (int mask)
{
  switch (kind)
    {
#if 0
    case item_monster:
      idai->select (mask);  // --fixme-- is this correct?
#endif
    case item_player:
      idplayer->select (mask);
    }
}


idEntity *item::getIdEntity (void)
{
  switch (kind)
    {
    case item_monster:
      return idai;
    case item_player:
      return idplayer;
    }
  assert (false);
  return NULL;
}


/*
 *  visibility
 */

idVec4 item::visibility (idVec4 value)
{
  switch (kind)
    {
#if 0
    case item_monster:
      // --fixme-- finish for monsters
#endif
    case item_player:
      return idplayer->SetVisibility (value);
    }
  assert (false);
  value.Zero ();
  return value;
}

/*
 *  visibilityParameters - returns the visibility parameters for id,
 *                         it also sets the new visibility parameters for id to value.
 */

idVec4 item::visibilityParameters (idVec4 value)
{
  switch (kind)
    {
#if 0
    case item_monster:
      // --fixme-- finish for monsters
#endif
    case item_player:
      return idplayer->SetVisibilityParameters (value);
    }
  assert (false);
  value.Zero ();
  return value;
}

/*
 *  visibilityFlag
 */

bool item::visibilityFlag (bool value)
{
  switch (kind)
    {
#if 0
    case item_monster:
      // --fixme-- finish for monsters
#endif
    case item_player:
      return idplayer->SetVisibilityFlag (value);
    }
  assert (false);
  return false;
}


void item::getSelfEntityNames (char *buffer, int length)
{
  switch (kind)
    {
#if 0
    case item_monster:
      // --fixme-- finish for monsters
      break;
#endif
    case item_player:
      idplayer->GetSelfEntityNames (buffer, length);
      break;
    }
}


int item::setVisibilityShader (char *buffer)
{
  switch (kind)
    {
#if 0
    case item_monster:
      // --fixme-- finish for monsters
      break;
#endif
    case item_player:
      return idplayer->SetVisibilityShader (buffer);
      break;
    }
  assert (false);
  return 0;
}

int item::flipVisibility (void)
{
  switch (kind)
    {
#if 0
    case item_monster:
      // --fixme-- finish for monsters
      break;
#endif
    case item_player:
      return idplayer->FlipVisibility ();
    }
  return -1;
}


#define MAX_ENTRY 1000

class dict
{
 public:
  dict (void);
  ~dict (void);
  dict (const dict &from);

  int add (const char *name, idAI *idBot, int instance);
  int add (const char *name, idPlayer *ip, int instance);
  int checkId (int id);
  idVec3 getPos (int id);
  bool stepDirection (int id, float dir);
  int stepForward (int id, int vel, int units);
  int stepRight (int id, int vel, int dist);
  int stepVec (int id, int velforward, int velright, int dist);
  int start_firing (int id);
  int stop_firing (int id);
  int reload_weapon (int id);
  int ammo (int id, int weapon_number);
  int stepUp (int id, int vel, int dist);
  int health (int id);
  int angle (int id);
  bool aim (int id, int enemy);
  int turn (int id, int angle, int angle_vel);
  void select (int id, int mask);
  int getHigh (void);
  int determineInstanceId (const char *name);
  bool canSeeEntity (int id, int entNo);
  idVec4 visibility (int id, idVec4 value);
  idVec4 visibilityParameters (int id, idVec4 value);
  bool visibilityFlag (int id, bool value);
  void getSelfEntityNames (int id, char *buffer, int length);
  int setVisibilityShader (int id, char *buffer);
  int flipVisibility (int id);
  int inventoryWeapon (int id, int weapon_number);
  int changeWeapon (int id, int weapon_number);
  int dropWeapon (int id);
 private:
  item *entry[MAX_ENTRY];
  int high;
};


dict::dict (void)
  : high (1)
{
}


dict::~dict (void)
{
}


dict::dict (const dict &from)
{
  *this = from;
}


int dict::determineInstanceId (const char *name)
{
  int instanceId = 0;
  int i = 0;

  while (i < high)
    {
      if ((entry[i] != NULL) && (strcmp (entry[i]->getName (), name) == 0))
	instanceId++;
      i++;
    }
  return instanceId;
}


/*
 *  add - add a new monster entry into our dictionary of items.
 *        Return the entry index (rid) used to contain the new item.
 */

int dict::add (const char *name, idAI *idBot, int instance)
{
  if (high == MAX_ENTRY)
    ERROR ("increase MAX_ENTRY");
  /*
   *  id of zero is not used.
   */
  int lastused = high;
  // int instance = determineInstanceId (name);
  entry[lastused] = new item (name, idBot, instance);
  high++;
  return lastused;
}


/*
 *  add - add a new monster entry into our dictionary of items.
 *        Return the entry index (rid) used to contain the new item.
 */

int dict::add (const char *name, idPlayer *ip, int instance)
{
  if (high == MAX_ENTRY)
    ERROR ("increase MAX_ENTRY");
  /*
   *  id of zero is not used.
   */
  int lastused = high;
  // int instance = determineInstanceId (name);
  entry[lastused] = new item (name, ip, instance);
  high++;
  return lastused;
}


int dict::checkId (int id)
{
  if (id < MAX_ENTRY)
    return id;
  return 0;
}


idVec3 dict::getPos (int id)
{
  return entry[id]->getPos ();
}


/*
 *  stepDirection - step forward
 */

bool dict::stepDirection (int id, float dir)
{
  return entry[id]->stepDirection (dir);
}


/*
 *  stepRight - step right by, units.
 */

int dict::stepRight (int id, int vel, int dist)
{
  return entry[id]->stepRight (vel, dist);
}


/*
 *  stepForward - step right by, units.
 */

int dict::stepForward (int id, int vel, int dist)
{
  return entry[id]->stepForward (vel, dist);
}


/*
 *  stepVec - step forward and right simulataneously by dist units.
 */

int dict::stepVec (int id, int velforward, int velright, int dist)
{
  return entry[id]->stepVec (velforward, velright, dist);
}


/*
 *  start_firing - fire the weapon.
 */

int dict::start_firing (int id)
{
  return entry[id]->start_firing ();
}


/*
 *  stop_firing - stop firing the weapon.
 */

int dict::stop_firing (int id)
{
  return entry[id]->stop_firing ();
}


/*
 *  ammo - return the ammo available for weapon_number.
 */

int dict::ammo (int id, int weapon_number)
{
  return entry[id]->ammo (weapon_number);
}


/*
 *  stepUp - steps up at speed, vel, over a, dist.
 */

int dict::stepUp (int id, int vel, int dist)
{
  return entry[id]->stepUp (vel, dist);
}


/*
 *  health - return the health for the bot.
 */

int dict::health (int id)
{
  return entry[id]->health ();
}


/*
 *  angle - return the angle (yaw) for the bot.
 */

int dict::angle (int id)
{
  return entry[id]->angle ();
}


/*
 *  aim - try and aim at enemy.
 *        If enemy is line of sight visible return true
 *        else return false.
 */

bool dict::aim (int id, int enemy)
{
  if (enemy <= maxId)
    return entry[id]->aim (entry[enemy]->getIdEntity ());
  else
    return entry[id]->aim (gameLocal.GetEntity (enemy));
}


/*
 *  turn - turn bot to face, angle.  It returns the current angle
 *         of the bot.
 */

int dict::turn (int id, int angle, int angle_vel)
{
  return entry[id]->turn (angle, angle_vel);
}


/*
 *  select - wait for bot id to complete any activity defined in mask.
 */

void dict::select (int id, int mask)
{
  entry[id]->select (mask);
}


/*
 *  getHigh - return the last legal id in the dictionary.
 */

int dict::getHigh (void)
{
  return high-1;
}


/*
 *  canSeeEntity - returns true if bot id can see entity entNo.
 */

bool dict::canSeeEntity (int id, int entNo)
{
  return entry[id]->canSeeEntity (entNo);
}


/*
 *  visibility - returns the old alpha value for id,
 *               it also sets the new alpha for id to value.
 */

idVec4 dict::visibility (int id, idVec4 value)
{
  return entry[id]->visibility (value);
}


/*
 *  visibilityParameters - returns the visibility parameters for id,
 *                         it also sets the new visibility parameters for id to value.
 */

idVec4 dict::visibilityParameters (int id, idVec4 value)
{
  return entry[id]->visibilityParameters (value);
}

/*
 *  visibilityFlag - returns the old bool value for id,
 *                   it also sets the new bool for id to value.
 */

bool dict::visibilityFlag (int id, bool value)
{
  return entry[id]->visibilityFlag (value);
}


/*
 *  setSelfEntityNames - add the list of entity names which the bot owns
 *                       to the buffer/length.  The entity names include body
 *                       components:  head, body, weapon etc.  Anything which
 *                       makes up a bot player figure.
 */

void dict::getSelfEntityNames (int id, char *buffer, int length)
{
  entry[id]->getSelfEntityNames (buffer, length);
}


/*
 *  setSelfEntityNames - add the list of entity names which the bot owns
 */

int dict::setVisibilityShader (int id, char *buffer)
{
  entry[id]->setVisibilityShader (buffer);
  return 0;
}


int dict::flipVisibility (int id)
{
  return entry[id]->flipVisibility ();
}


int dict::inventoryWeapon (int id, int weapon_number)
{
  return entry[id]->inventoryWeapon (weapon_number);
}


int dict::changeWeapon (int id, int weapon_number)
{
  return entry[id]->changeWeapon (weapon_number);
}


int dict::dropWeapon (int id)
{
  return entry[id]->dropWeapon ();
}


/*
 *  reload_weapon
 */

int dict::reload_weapon (int id)
{
  return entry[id]->reload_weapon ();
}


static dict *dictionary = NULL;


void initialise_dictionary (void)
{
  if (dictionary == NULL)
    dictionary = new dict ();
}


int checkId (int id)
{
  initialise_dictionary ();
  return dictionary->checkId (id);
}


int define (const char *name, idAI *idBot, int instance)
{
  initialise_dictionary ();
  return dictionary->add (name, idBot, instance);
}


int define (const char *name, idPlayer *ip, int instance)
{
  initialise_dictionary ();
  return dictionary->add (name, ip, instance);
}


class pyList
{
public:
  pyList (void);
  ~pyList (void);
  pyList (const pyList &from);

  void include (pyBotClass *p, int id);
  pyBotClass *remove (const char *name, int id);
  pyBotClass *lookup (const char *name, int id);
private:
  pyBotClass *content[MAX_PYLIST];
  int         ids[MAX_PYLIST];
  int high;
  int used;
};

pyList::pyList (void)
  : high (0), used (0)
{
}

pyList::~pyList (void)
{
}

pyList::pyList (const pyList &from)
{
  *this = from;
}


void pyList::include (pyBotClass *p, int id)
{
  /*
   *  have we already stored p?  if so we return.
   */
  for (int i = 0; i < high; i++)
    {
      if ((content[i] == p) && (ids[i] == id))
	return;   /* already stored, we are done.  */
    }
  if (used == MAX_PYLIST)
    ERROR ("increase MAX_PYLIST");
  /*
   *  check to reuse an empty slot.
   */
  for (int i = 0; i < high; i++)
    {
      if (content[i] == NULL)
	{
	  content[i] = p;
	  ids[i] = id;
	  used++;
	  return;
	}
    }
  /*
   *  we have to use a new slot.
   */
  content[high] = p;
  ids[high] = id;
  high++;
  used++;
}


/*
 *  remove - attempt to remove bot with a name from the pyList.
 *           NULL is returned if unsuccessful.
 */

pyBotClass *pyList::remove (const char *name, int id)
{
  for (int i = 0; i < high; i++)
    {
      gameLocal.Printf ("looking for name = %s and id = %d\n", name, id);
      if (content[i] != NULL)
	{
	  gameLocal.Printf ("  slot %i has name = %s and id = %d\n",
			    i, content[i]->getName (), ids[i]);
	}
      if ((content[i] != NULL)
	  && (strcmp (name, content[i]->getName ()) == 0)
	  && (ids[i] == id))
	{
	  pyBotClass *p = content[i];
	  content[i] = NULL;
	  ids[i] = -1;
	  used--;
	  gameLocal.Printf ("buffer [%d] = %s %d found\n", i, p->getName (), id);
	  return p;
	}
    }
  return NULL;
}

/*
 *  lookup - the bot with a name from the pyList.
 *           NULL is returned if unsuccessful.
 */

pyBotClass *pyList::lookup (const char *name, int id)
{
  for (int i = 0; i < high; i++)
    {
      gameLocal.Printf ("looking for name = %s and id = %d\n", name, id);
      if (content[i] != NULL)
	{
	  gameLocal.Printf ("  slot %i has name = %s and id = %d\n",
			    i, content[i]->getName (), ids[i]);
	}
      if ((content[i] != NULL)
	  && (strcmp (name, content[i]->getName ()) == 0)
	  && (ids[i] == id))
	{
	  pyBotClass *p = content[i];
	  return p;
	}
    }
  return NULL;
}

/***********************************************************************/
/* end of test */
/***********************************************************************/

/*
 *  list of pending bots which have been partially connected.
 *  This is necessary as the clients might try and connect in any order.
 *  Whereas the map creation will want a specific bot.
 */

static pyList pending;

/*
 *  active list contains all pybots which have been attached
 *  to their python clients.
 */
static pyList active;

/*
 *  allbots contains a list of all Python bots and it is used to obtain
 *  the pyBotClass object given a name and instance number.
 */

static pyList allbots;


pyBufferClass::pyBufferClass (void)
  : rin (0), win (0), wout (0), wsize (0)
{
}


pyBufferClass::~pyBufferClass (void)
{
}


pyBufferClass::pyBufferClass (const pyBufferClass &from)
{
  *this = from;
}


char *pyBufferClass::pyread (int fd, bool canBlock)
{
  fd_set inset;
  int n;

  while (true)
    {
      FD_ZERO (&inset);
      FD_SET (fd, &inset);
      if (canBlock)
	select (fd+1, &inset, NULL, NULL, NULL);
      else
	{
	  struct timeval timeout;
	  timeout.tv_sec = 0;
	  timeout.tv_usec = 0;
	  select (fd+1, &inset, NULL, NULL, &timeout);
	}

      if (FD_ISSET (fd, &inset)) {
	n = read (fd, &rBuffer[rin], MAX_PY_BUFFER-rin);
	if (n > 0)
	  {
	    int t = rin + n;
	    for (int i = rin; i < t; i++)
	      if (rBuffer[i] == '\n')
		{
		  /*
		   *  end of line.  Return this and reset input.
		   */
		  rBuffer[i] = (char)0;  /* convert the '\n' into '\0'.  */
		  rin += n;
		  rBuffer[rin] = (char)0;  /* null terminate the buffer for debugging purposes.  */
		  rin = 0;
                  if (protocol_debugging)
                    {
                      gameLocal.Printf ("rBuffer is now: ");
                      gameLocal.Printf (rBuffer);
                    }
		  return &rBuffer[0];
		}
	    /*
	     *  partial line read, continue reading later.
	     */
	    rin += n;
	  }
	else
	  return NULL;
      } else
	return NULL;
    }
  return NULL;
}


void pyBufferClass::pyput (char *output)
{
  for (int i = 0; i < strlen (output); i++)
    pyputChar (output[i]);
}


void pyBufferClass::pyputChar (char ch)
{
  if (wsize == MAX_PY_BUFFER)
    ERROR ("increase MAX_PY_BUFFER");
  wBuffer[win] = ch;
  win = (win + 1) % MAX_PY_BUFFER;
  wsize++;
}


bool pyBufferClass::pyflushed (int fd, bool canBlock)
{
  if (wsize == 0)
    return true;

  fd_set outset;
  int n;

  while (wout < wsize) {
    FD_ZERO (&outset);
    FD_SET (fd, &outset);
    if (canBlock)
      select (fd+1, NULL, &outset, NULL, NULL);
    else {
      struct timeval timeout;
      timeout.tv_sec = 0;
      timeout.tv_usec = 0;
      select (fd+1, NULL, &outset, NULL, &timeout);
    }

    if (FD_ISSET (fd, &outset)) {
      if (protocol_debugging)
	{
	  for (int i = wout; i < wsize-wout; i++)
	    {
	      gameLocal.Printf ("buffer sending %c\n", wBuffer[i]);
	    }
	}
      n = write (fd, &wBuffer[wout], wsize-wout);
      if (n > 0)
	wout += n;
      else
	return false;
    } else
      return false;
  }
  wout = 0;
  wsize = 0;
  win = 0;
  return true;
}

/* ok */

pyServerClass::pyServerClass (void)
  : enabled (false), state (toInit)
{
  connectedBot = NULL;
  connectFd = -1;
}


pyServerClass::~pyServerClass (void)
{
}


pyServerClass::pyServerClass (const pyServerClass &from)
{
  *this = from;
}


void checkInitialiseSuper (void)
{
  if (super == NULL)
    super = new pyServerClass ();
}


/*
 *  poll the super server.
 */

void poll (bool canBlock)
{
  checkInitialiseSuper ();
  super->poll (canBlock);
}


void pyServerClass::initServer (void)
{
  superServerPort = tryActivate (superServerPort);
}


void pyServerClass::poll (bool canBlock)
{
  switch (state) {

  case toInit:
    initServer ();
    break;
  case toAccept:
    acceptServer (canBlock);
    break;
  case toRead:
    readServer (canBlock);
    break;
  case toWrite:
    writeServer (canBlock);
    break;
  case toWriteConnected:
    writeConnectedServer (canBlock);
    break;
  case toClose:
    closeServer (canBlock);
    break;
  default:
    ERROR ("unrecognised state");
  }
}


/*
 *  tryActivate - try and use desiredPort when starting a socket server.
 */

int pyServerClass::tryActivate (int desiredPort)
{
  struct hostent *hp;
  char hostname[HOST_NAME_MAX];

  if (gethostname (hostname, HOST_NAME_MAX) < 0)
    ERROR ("cannot find our hostname (is networking operational on this machine?)");

  hp = gethostbyname (hostname);

  int n = 0;
  int b;
  do {
    /*
     *  open a TCP socket (an Internet stream socket)
     */

    socketFd = socket (hp->h_addrtype, SOCK_STREAM, 0);
    if (socketFd < 0)
      ERROR ("socket");

    socklen_t s = sizeof (sa);

    memset (&sa, 0, s);
    assert ((hp->h_addrtype == AF_INET));
    sa.sin_family      = hp->h_addrtype;
    sa.sin_addr.s_addr = htonl (INADDR_ANY);
    sa.sin_port        = htons (desiredPort);

    b = bind (socketFd, (struct sockaddr *)&sa, s);

    if (b < 0) {
      gameLocal.Printf ("unable to bind python socket to the desired port %d\n",
			desiredPort);
      n++;
      desiredPort++;
    }
  } while ((b < 0) && (n < MAX_PY_SERVERS));

  if (b < 0)
    ERROR ("cannot bind to any socket on this machine");

  gameLocal.Printf ("waiting for python bot to connect on port %d\n", desiredPort);
  listen (socketFd, 1);
  state = toAccept;
  return desiredPort;
}


void pyServerClass::acceptServer (bool canBlock)
{
  socklen_t n = sizeof (isa);
  assert (connectFd == -1);
  connectFd = accept (socketFd, (struct sockaddr *)&isa, &n);
  if (connectFd < 0)
    ERROR ("accept");

  state = toRead;
}


void pyServerClass::readServer (bool canBlock)
{
  char *data = buffer.pyread (connectFd, canBlock);  /* data contains the bot name or "super"  */

  if (data != NULL)
    {
      char portValue[20];
      if (strcmp (data, "super") == 0)
	{
	  gameLocal.Printf ("bot wants to know the superserver port (which is %d)\n",
			    superServerPort);
	  /*
	   *  found query for superServer port
	   */
	  idStr::snPrintf (portValue, sizeof (portValue), "%d\n", superServerPort);
	  buffer.pyput (portValue);
	  state = toWrite;
	}
      else
	{
	  gameLocal.Printf ("bot %s wants to connect\n", data);
	  /*
	   *  python bot want us to create a bot and tell the script which portno
	   *  has been allocated.
	   */
	  int portno;
	  int botInstanceId = -1;
	  char *botname = strdup (data);
	  char *idstr = index (botname, ' ');

	  if ((idstr != NULL) && ((*idstr) != (char)0))
	    botInstanceId = atoi (idstr);

	  if (botInstanceId == -1)
	    gameLocal.Printf ("incorrect bot id, bot name sent from python client %s has id of -1\n", data);
	  *idstr = (char)0;
	  connectedBot = new pyBotClass ();
	  connectedBot->setName (botname);
	  connectedBot->setInstanceId (botInstanceId);
	  connectedBot->initServer (0);  /* any available port is good.  */
	  portno = connectedBot->getPortNo ();
	  gameLocal.Printf ("bot %s instance %d has been allocated port %d\n",
			    idstr, botInstanceId, portno);
	  idStr::snPrintf (portValue, sizeof (portValue), "%d\n", portno);
	  buffer.pyput (portValue);
	  state = toWriteConnected;
	}
    }
}


/*
 *  writeServer
 */

void pyServerClass::writeServer (bool canBlock)
{
  if (buffer.pyflushed (connectFd, canBlock))
    state = toClose;
}


/*
 *  writeConnectedServer
 */

void pyServerClass::writeConnectedServer (bool canBlock)
{
  if (buffer.pyflushed (connectFd, canBlock))
    {
      state = toClose;
      connectedBot->setConnected ();
      pending.include (connectedBot, connectedBot->getInstanceId ());
      connectedBot = NULL;
      gameLocal.Printf ("bot port has been flushed to the script\n");
    }
}


/*
 *  closeServer
 */

void pyServerClass::closeServer (bool canBlock)
{
  if (buffer.pyflushed (connectFd, canBlock))
    {
      close (connectFd);
      state = toAccept;
      connectFd = -1;
    }
}


/*
 *  developerHelp - writes out some interactive help to prompt the developer to manually connect
 *                  a Python bot.
 */

void developerHelp (const char *name)
{
  char buffer[HOST_NAME_MAX];
  int result = gethostname (buffer, sizeof (buffer));

  gameLocal.Printf ("bot %s is ready to be controlled by Python\n", name);
  gameLocal.Printf ("suggest that you run the following from the command line\npython %s/%s/%s.py\n", getHome (), getDir (), name);
  if (result < 0)
    gameLocal.Printf ("developer needs to run the Python script from the terminal connecting to localhost:%d", superServerPort);
  else
    gameLocal.Printf ("developer needs to run the Python script from the terminal connecting to %s:%d",
	    buffer, superServerPort);
}


/*
 *  forkscript - if in developer mode call developerHelp otherwise fork and exec a python script.
 */

void forkScript (const char *name, int id)
{
  if (getenv ("DEBUG_PYBOT") == NULL)
    {
      char buffer[PATH_MAX];
      char idtext[MAX_ID_STR];

      idStr::snPrintf (buffer, sizeof (buffer), "%s/%s/%s.py", getHome (), getDir (), name);
      idStr::snPrintf (idtext, sizeof (idtext), "%d", id);
      gameLocal.Printf ("execl /usr/bin/python %s %d\n", buffer, id);
      int pid = fork ();
      if (pid == 0)
	/* child process.  */
	{
	  int r = execl ("/usr/bin/python3", "python3", buffer, idtext, (char *)NULL);

	  if (r != 0)
	    perror ("execl");
	}
      else
	/* --fixme-- add pid to list of pids and kill them off at the end of the game.  */
	;
    }
  else
    developerHelp (name);
}


static void mystop (void) {}


/*
 *  populateDictionary - adds idBot into the python bot universe of objects.
 */

void populateDictionary (const char *name, idAI *idBot, int instance)
{
  define (name, idBot, instance);
}

/*
 *  populateDictionary - adds idBot into the python bot universe of objects.
 */

void populateDictionary (const char *name, idPlayer *ip, int instance)
{
  define (name, ip, instance);
}


/*
 *  doRegisterName - registers the bot with the python client.
 *                   We create a server and tell the super server
 *                   which port we are using.
 *                   This bot (player/monster) is completely controlled via Python.
 *                   name is the script to be run and the, instance.
 */

pyBotClass *doRegisterName (const char *name, int instance, int rid)
{
  pyBotClass *b;

  gameLocal.Printf ("real registerName reached!\n");
  forkScript (name, instance);
  gameLocal.Printf ("registerName is wanting to connect with a script called '%s' instance %d\n", name, instance);
  do {
    b = pending.remove (name, instance);
    if (b == NULL)
      poll (true);
  } while (b == NULL);
  active.include (b, instance);
  allbots.include (b, instance);
  b->setInstanceId (instance);
  b->setRpcId (rid);
  gameLocal.Printf ("registerName completing after successfully connecting with the script '%s' instance %d\n", name, instance);
  if (rid > maxId)
    maxId = rid;
  return b;
}


/*
 *  registerName - the map has requested a Python monster bot.
 *                 We create a server and tell the super server which port we are using.
 */

pyBotClass *registerName (const char *name, idAI *idBot, int instance)
{
  return doRegisterName (name, instance, define (name, idBot, instance));
}


/*
 *  registerName - the map has requested a Python player bot.
 *                 We create a server and tell the super server
 *                 which port we are using.
 *                 This bot is completely controlled via Python
 *                 and no user input is used.
 */

pyBotClass *registerName (const char *name, idPlayer *ip, int instance)
{
  return doRegisterName (name, instance, define (name, ip, instance));
}


/*
 *  deRegisterName - the bot has died and we need to deregister its name.
 */

pyBotClass *deRegisterName (const char *name, idPlayer *idBot, int instance)
{
  pyBotClass *b = active.lookup (name, instance);
  pending.include (b, instance);
  b->forceClose ();
  return b;
}


/*
 *  lookupName - returns the pyBotClass associated with, name, and, instance.
 */

pyBotClass *lookupName (const char *name, int instance)
{
  return allbots.lookup (name, instance);
}


pyBotClass::pyBotClass ()
  : instanceId (-1), rpcId (0), name (NULL), portNo (0), enabled (false), state (toInit),
    socketFd (0), connectFd (0), connected (false)
{
}


pyBotClass::~pyBotClass ()
{
}


pyBotClass::pyBotClass (const pyBotClass &from)
{
  *this = from;
}


int pyBotClass::getPortNo (void)
{
  return portNo;
}


bool pyBotClass::getConnected (void)
{
  checkInitialiseSuper ();
  super->poll (false);
  return connected;
}


void pyBotClass::setConnected (void)
{
  gameLocal.Printf ("setConnected has been called\n");
  mystop ();
  connected = true;
}


void pyBotClass::initServer (int desiredPort)
{
  int p;
  if (desiredPort > 0)
    {
      do {
	p = tryActivate (desiredPort);
	if (p == 0)
	  {
	    gameLocal.Printf ("waiting for port %d to become available...\n", desiredPort);
	    sleep (1);
	  }
      } while (p == 0);
    }
  else
    {
      desiredPort = superServerPort+1;
      do {
	p = tryActivate (desiredPort);
	desiredPort++;
      } while (p == 0);
    }
  portNo = p;
}


/*
 *  tryActivate - try and use desiredPort when starting a socket server.
 */

int pyBotClass::tryActivate (int desiredPort)
{
  struct hostent *hp;
  int b;
  char hostname[HOST_NAME_MAX];

  if (gethostname (hostname, HOST_NAME_MAX) < 0)
    ERROR ("cannot find our hostname (is networking operational on this machine?)");

  hp = gethostbyname (hostname);

  /*
   *  open a TCP socket (an Internet stream socket)
   */

  socketFd = socket (hp->h_addrtype, SOCK_STREAM, 0);
  if (socketFd < 0)
    ERROR ("socket");

  memset (&sa, 0, sizeof (sa));
  assert ((hp->h_addrtype == AF_INET));
  sa.sin_family      = hp->h_addrtype;
  sa.sin_addr.s_addr = htonl (INADDR_ANY);
  sa.sin_port        = htons (desiredPort);

  b = bind (socketFd, (struct sockaddr *)&sa, sizeof (sa));

  if (b < 0) {
    debugf ("unable to bind python socket to the desired port\n");
    return 0;
  }
  else
    {
      gameLocal.Printf ("waiting for python bot to connect on port %d\n", desiredPort);
      listen (socketFd, 1);
      state = toAccept;
    }
  return desiredPort;
}


/*
 *  acceptServer - bot performs an accept and obtains the connectFd socket for all
 *                 remaining communication with the python script.
 */

void pyBotClass::acceptServer (bool canBlock)
{
  socklen_t n = sizeof (isa);
  connectFd = accept (socketFd, (struct sockaddr *)&isa, &n);
  if (connectFd < 0)
    ERROR ("accept");

  state = toRead;
}


/*
 *  readServer - tries to obtain a command from the python script and if successful
 *               it interprets the remote procedure call.
 */

void pyBotClass::readServer (bool canBlock, bool dead)
{
  char *data = buffer.pyread (connectFd, canBlock);  /* data contains the bot name or "super"  */

  if ((data != NULL) && (! dead))
    interpretRemoteProcedureCall (data);
}


/*
 *  setRpcId - assign, rpcId, to, id.
 */

void pyBotClass::setRpcId (int id)
{
  rpcId = id;
}

/*
 *  getRpcId - return bots python id.
 */

int pyBotClass::getRpcId (void)
{
  return rpcId;
}

/*
 *  setInstanceId - assign, instanceId, to, id.
 */

void pyBotClass::setInstanceId (int id)
{
  instanceId = id;
}

/*
 *  getInstanceId - return bots python id.
 */

int pyBotClass::getInstanceId (void)
{
  return instanceId;
}

/*
 *  interpretRemoteProcedureCall - a switch statement of all rpc commands.
 */

void pyBotClass::interpretRemoteProcedureCall (char *data)
{
  if (protocol_debugging)
    gameLocal.Printf ("rpc (%s)\n", data);
  if (strcmp (data, "super") == 0)
    rpcSuper ();
  else if (idStr::Cmpn (data, "getpos ", 7) == 0)   // Id's strncmp equivalent
    rpcGetPos (&data[7]);
  else if (strcmp (data, "self") == 0)
    rpcSelf ();
  else if (strcmp (data, "health") == 0)
    rpcHealth ();
  else if (strcmp (data, "maxobj") == 0)
    rpcMaxObj ();
  else if (idStr::Cmpn (data, "step ", 5) == 0)
    rpcStep (&data[5]);
  else if (idStr::Cmpn (data, "right ", 6) == 0)
    rpcRight (&data[6]);
  else if (idStr::Cmpn (data, "forward ", 8) == 0)
    rpcForward (&data[8]);
  else if (idStr::Cmpn (data, "stepvec ", 8) == 0)
    rpcStepVec (&data[8]);
  else if (strcmp (data, "start_firing") == 0)
    rpcStartFiring ();
  else if (strcmp (data, "stop_firing") == 0)
    rpcStopFiring ();
  else if (strcmp (data, "reload_weapon") == 0)
    rpcReloadWeapon ();
  else if (idStr::Cmpn (data, "ammo ", 5) == 0)
    rpcAmmo (&data[5]);
  else if (idStr::Cmpn (data, "step_up", 7) == 0)
    rpcStepUp (&data[7]);
  else if (idStr::Cmpn (data, "aim ", 4) == 0)
    rpcAim (&data[4]);
  else if (idStr::Cmpn (data, "turn ", 5) == 0)
    rpcTurn (&data[5]);
  else if (strcmp (data, "angle") == 0)
    rpcAngle ();
  else if (idStr::Cmpn (data, "tag ", 4) == 0)
    rpcTag (&data[4]);
  else if (idStr::Cmpn (data, "select ", 7) == 0)
    rpcSelect (&data[7]);
  else if (idStr::Cmpn (data, "get_class_name_entity ", 22) == 0)
    rpcGetClassNameEntity (&data[22]);
  else if (idStr::Cmpn (data, "get_pair_name_entity ", 21) == 0)
    rpcGetPairEntity (&data[21]);
  else if (idStr::Cmpn (data, "get_entity_pos ", 15) == 0)
    rpcGetEntityPos (&data[15]);
  else if (idStr::Cmpn (data, "get_entity_name ", 16) == 0)
    rpcGetEntityName (&data[16]);
  else if (idStr::Cmpn (data, "change_weapon ", 14) == 0)
    rpcChangeWeapon (&data[14]);
  else if (idStr::Cmpn (data, "can_see_entity ", 15) == 0)
    rpcCanSeeEntity (&data[15]);
  else if (idStr::Cmpn (data, "map_to_runtime_entity ", 21) == 0)
    rpcMapToRunTimeEntity (&data[21]);
  else if (idStr::Cmpn (data, "visibility ", 11) == 0)
    rpcVisibility (&data[11]);
  else if (idStr::Cmpn (data, "visibilityflag ", 15) == 0)
    rpcVisibilityFlag (&data[15]);
  else if (strcmp (data, "getselfentitynames") == 0)
    rpcGetSelfEntityNames ();
  else if (idStr::Cmpn (data, "setvisibilityshader ", 20) == 0)
    rpcSetVisibilityShader (&data[20]);
  else if (idStr::Cmpn (data, "visibilityparams ", 17) == 0)
    rpcVisibilityParameters (&data[17]);
  else if (strcmp (data, "flipvisibility") == 0)
    rpcFlipVisibility ();
  else if (idStr::Cmpn (data, "inventory_weapon ", 17) == 0)
    rpcInventoryWeapon (&data[17]);
  else if (strcmp (data, "drop_weapon") == 0)
    rpcDropWeapon ();
  else
    {
      gameLocal.Printf ("data = \"%s\", len (data) = %d\n", data, (int) strlen (data));
      ERROR ("unrecognised rpc command");
    }
}


/*
 *  rpcSuper - handle the request for the superserver portno.
 */

void pyBotClass::rpcSuper (void)
{
  char portValue[20];

  gameLocal.Printf ("bot wants to know the superserver port (which is %d) interesting as this has been detected by a botserver\n", superServerPort);
  /*
   *  found query for superServer port, respond appropriately
   */
  idStr::snPrintf (portValue, sizeof (portValue), "%d\n", superServerPort);
  buffer.pyput (portValue);
  state = toWrite;
}


/*
 *  rpcGetPos - generate an x, y, z string and send it back to the script.
 *              The parameter, data, contains the id.
 */

void pyBotClass::rpcGetPos (char *data)
{
  if (protocol_debugging)
    gameLocal.Printf ("rpcGetPos (%s) call by python\n", data);

  char buf[1024];
  int id = checkId (atoi (data));

  if (id > 0)
    {
      if (id <= maxId)
	{
	  /* A pybot or human player.  */
	  const idVec3 &org = dictionary->getPos (id);
	  idStr::snPrintf (buf, sizeof (buf), "%g %g %g\n",
			   org.x, org.y, org.z);
	}
      else
	if (id < gameLocal.num_entities)
	  {
	    /* A doom3 entity.  */
	    const idVec3 &org = gameLocal.entities[id]->GetPhysics ()->GetOrigin ();
	    idStr::snPrintf (buf, sizeof (buf), "%g %g %g\n",
			     org.x, org.y, org.z);
	  }
      	else
	  strcpy (buf, "None\n");
    }
  else
    strcpy (buf, "None\n");
  if (protocol_debugging)
    gameLocal.Printf ("rpcGetPos responding with: %s\n", buf);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcSelf - return our id.
 */

void pyBotClass::rpcSelf (void)
{
  char buf[1024];

  if (protocol_debugging)
    gameLocal.Printf ("rpcSelf \n");
  idStr::snPrintf (buf, sizeof (buf), "%d\n", rpcId);
  if (protocol_debugging)
    gameLocal.Printf ("rpcSelf responding with: %s\n", buf);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcHealth - return our health.
 */

void pyBotClass::rpcHealth (void)
{
  char buf[1024];

  if (protocol_debugging)
    gameLocal.Printf ("rpcHealth \n");
  idStr::snPrintf (buf, sizeof (buf), "%d\n", dictionary->health (rpcId));
  if (protocol_debugging)
    gameLocal.Printf ("rpcHealth responding with: %s\n", buf);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcMaxObj - return the maximum number of ids in the dictionary.
 *              Indicates that 1..high can all be accessed.
 */

void pyBotClass::rpcMaxObj (void)
{
 char buf[1024];

 initialise_dictionary ();
 idStr::snPrintf (buf, sizeof (buf), "%d\n", dictionary->getHigh ());
 buffer.pyput (buf);
 state = toWrite;
}


/*
 *  rpcStep - step forward direction
 *            The parameter, data, contains the direction.
 */

void pyBotClass::rpcStep (char *data)
{
  char buf[1024];
  bool done = false;

  if (protocol_debugging)
    gameLocal.Printf ("rpcStep (%s) call by python\n", data);

  if (rpcId > 0)
    {
      float dir = atof (data);
      done = dictionary->stepDirection (rpcId, dir);
    }
  if (done)
    strcpy (buf, "true\n");
  else
    strcpy (buf, "false\n");
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcRight - step right.
 *             The parameter, data, contains two parameters:  velocity and distance.
 */

void pyBotClass::rpcRight (char *data)
{
  char buf[1024];
  int vel = 0;
  int dist = 0;

  if (protocol_debugging)
    gameLocal.Printf ("rpcRight (%s) call by python\n", data);

  if (rpcId > 0)
    {
      vel = atoi (data);
      char *p = index (data, ' ');
      if ((p == NULL) || ((*p) == '\0'))
	dist = 0;
      else
	dist = atoi (p);
      dist = dictionary->stepRight (rpcId, vel, dist);
    }
  idStr::snPrintf (buf, sizeof (buf), "%d\n", dist);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcForward - step forward.
 *               The parameter, data, contains two parameters:  velocity and distance.
 */

void pyBotClass::rpcForward (char *data)
{
  char buf[1024];
  int vel = 0;
  int dist = 0;

  if (protocol_debugging)
    gameLocal.Printf ("rpcForward (%s) call by python\n", data);

  if (rpcId > 0)
    {
      vel = atoi (data);
      char *p = index (data, ' ');
      if ((p == NULL) || ((*p) == '\0'))
	dist = 0;
      else
	dist = atoi (p);
      dist = dictionary->stepForward (rpcId, vel, dist);
    }
  idStr::snPrintf (buf, sizeof (buf), "%d\n", dist);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcStepVec - step forward along a vector.
 *               The parameter, data, contains three parameters:
 *               velocity forward, velocity right and distance.
 */

void pyBotClass::rpcStepVec (char *data)
{
  char buf[1024];
  int velforward = 0;
  int velright = 0;
  int dist = 0;

  if (protocol_debugging)
    gameLocal.Printf ("rpcStepVec (%s) call by python\n", data);

  if (rpcId > 0)
    {
      velforward = atoi (data);
      char *p = index (data, ' ');
      if ((p == NULL) || ((*p) == '\0'))
	velright = 0;
      else
	{
	  velright = atoi (p);
	  char *p = index (data, ' ');
	  if ((p == NULL) || ((*p) == '\0'))
	    dist = atoi (p);
	}
      dist = dictionary->stepVec (rpcId, velforward, velright, dist);
    }
  idStr::snPrintf (buf, sizeof (buf), "%d\n", dist);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcAim - aim the weapon at, id.
 */

void pyBotClass::rpcAim (char *data)
{
  char buf[1024];
  int id = checkId (atoi (data));
  bool seen = false;

  if (protocol_debugging)
    gameLocal.Printf ("rpcAim (%s) \n", data);

  if (id > 0)
    seen = dictionary->aim (rpcId, id);
  if (seen)
    idStr::snPrintf (buf, sizeof (buf), "true\n");
  else
    idStr::snPrintf (buf, sizeof (buf), "false\n");
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcAngle - return the angle of the bot.
 */

void pyBotClass::rpcAngle (void)
{
  char buf[1024];

  if (protocol_debugging)
    gameLocal.Printf ("rpcAngle \n");

  int angle = dictionary->angle (rpcId);
  idStr::snPrintf (buf, sizeof (buf), "%d\n", angle);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcTurn - turn to face angle.
 */

void pyBotClass::rpcTurn (char *data)
{
  char buf[1024];
  int angle = 0;
  int vel = 0;

  if (protocol_debugging)
    gameLocal.Printf ("rpcAngle (%s) \n", data);

  if (rpcId > 0)
    {
      angle = atoi (data);
      char *p = index (data, ' ');
      if ((p == NULL) || ((*p) == '\0'))
	vel = 0;
      else
	vel = atoi (p);
      angle = dictionary->turn (rpcId, angle, vel);
    }

  idStr::snPrintf (buf, sizeof (buf), "%d\n", angle);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  truncstr - truncates string name by assigning (char)0 to every space or \n.
 */

char *pyBotClass::truncstr (char *name)
{
  int i = 0;
  int l = strlen (name);

  while (i < l)
    {
      if ((name[i] == ' ') || (name[i] == '\n'))
        name[i] = (char)0;
      i++;
    }
  return name;
}


/*
 *  rpcTag - request the tag definition of name from the .map file.
 */

void pyBotClass::rpcTag (char *name)
{
  char buf[1024];

  name = truncstr (name);
  if (protocol_debugging)
    gameLocal.Printf ("rpcTag %s \n", name);

  const char *p = gameLocal.FindDefinition (name);
  if (p == NULL)
    strcpy (buf, "\n");
  else
    idStr::snPrintf (buf, sizeof (buf), "%s\n", p);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcSelect - request we wait until some desired activity completes.
 */

void pyBotClass::rpcSelect (char *data)
{
  if (protocol_debugging)
    gameLocal.Printf ("rpcSelect (%s) \n", data);
  int mask = 0;

  if (strcmp (data, "any") == 0)
    mask = 0x0f;
  else
    mask = atoi (data);

  if (mask == 0 || rpcId == 0)
    {
      char buf[1024];

      idStr::snPrintf (buf, sizeof (buf), "0\n");
      buffer.pyput (buf);
      state = toWrite;
    }
  else
    {
      dictionary->select (rpcId, mask);
      state = toSelect;   /* move into the select state.  */
    }
}


/*
 *  rpcStartFiring - fire the weapon.
 */

void pyBotClass::rpcStartFiring (void)
{
  char buf[1024];
  int ammo;

  if (protocol_debugging)
    gameLocal.Printf ("rpcStartFiring call python\n");

  if (rpcId > 0)
    ammo = dictionary->start_firing (rpcId);
  else
    ammo = 0;

  idStr::snPrintf (buf, sizeof (buf), "%d\n", ammo);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcStopFiring - fire the weapon.
 */

void pyBotClass::rpcStopFiring (void)
{
  char buf[1024];
  int ammo;

  if (protocol_debugging)
    gameLocal.Printf ("rpcStopFiring call by python\n");

  if (rpcId > 0)
    ammo = dictionary->stop_firing (rpcId);
  else
    ammo = 0;

  idStr::snPrintf (buf, sizeof (buf), "%d\n", ammo);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcAmmo - return the amount of ammo available for the current weapon.
 */

void pyBotClass::rpcAmmo (const char *weapon_number)
{
  char buf[1024];
  int result = 0;

  if (protocol_debugging)
    gameLocal.Printf ("rpcAmmo %s\n", weapon_number);
  if (rpcId > 0)
    result = dictionary->ammo (rpcId, atoi (weapon_number));

  idStr::snPrintf (buf, sizeof (buf), "%d\n", result);
  if (protocol_debugging)
    gameLocal.Printf ("rpcAmmo responding with: %s\n", buf);
  buffer.pyput (buf);
  state = toWrite;
}

/*
 *  rpcStepUp
 */

void pyBotClass::rpcStepUp (char *data)
{
  if (protocol_debugging)
    gameLocal.Printf ("rpcStepUp call by python: %s\n", data);

  char buf[1024];
  int result;
  int dist = 0;
  int vel = atoi (data);

  if (rpcId > 0)
    {
      char *p = data;

      // skip spaces
      while ((p != NULL) && ((*p) != '\0') && ((*p) == ' '))
	p++;
      // now find the next space after the number.
      p = index (p, ' ');
      // after this space is the last number, dist
      if ((p != NULL) && ((*p) != '\0'))
	dist = atoi (p);
      result = dictionary->stepUp (rpcId, vel, dist);
    }

  idStr::snPrintf (buf, sizeof (buf), "%d\n", result);
  buffer.pyput (buf);
  state = toWrite;
}

/*
 *  rpcReloadWeapon - reload the weapon and return the amount of ammo available
 *                    for the current weapon after reloading.
 */

void pyBotClass::rpcReloadWeapon (void)
{
  char buf[1024];
  int ammo;

  if (protocol_debugging)
    gameLocal.Printf ("rpcReloadWeapon\n");

  if (rpcId > 0)
    ammo = dictionary->reload_weapon (rpcId);
  else
    ammo = 0;

  idStr::snPrintf (buf, sizeof (buf), "%d\n", ammo);
  buffer.pyput (buf);
  state = toWrite;
}


void pyBotClass::rpcInventoryWeapon (const char *weapon_number)
{
  char buf[1024];
  int result = 0;

  if (protocol_debugging)
    gameLocal.Printf ("rpcInventoryWeapon %s\n", weapon_number);
  if (rpcId > 0)
    result = dictionary->inventoryWeapon (rpcId, atoi (weapon_number));

  idStr::snPrintf (buf, sizeof (buf), "%d\n", result);
  if (protocol_debugging)
    gameLocal.Printf ("rpcInventoryWeapon responding with: %s\n", buf);
  buffer.pyput (buf);
  state = toWrite;
}


idVec4
pyBotClass::strToidVec4 (const char *value)
{
  idVec4 val;
  idStr str (value);
  idStr element;
  int i = 0;

  val.Zero ();
  while ((i < 4) && (str.Length () > 0))
    {
      element = str.CARWord ();
      if (element.Length () > 0)
	val[i] = atof (element.c_str ());
      i++;
      str = str.CDRWord ();
    }
  return val;
}


/*
 *  rpcVisibility - return the current level of visibility 0.0..1.0.
 *                  It also sets the current level of visibility to the float argument.
 */

void pyBotClass::rpcVisibility (const char *value)
{
  char buf[1024];
  idVec4 vis;

  vis.Zero ();
  if (protocol_debugging)
    gameLocal.Printf ("rpcVisibility %s\n", value);
  if (rpcId > 0)
    vis = dictionary->visibility (rpcId, strToidVec4 (value));

  idStr::snPrintf (buf, sizeof (buf), "%f %f %f %f\n",
		   vis[0], vis[1], vis[2], vis[3]);
  if (protocol_debugging)
    gameLocal.Printf ("rpcVisibility responding with: %s\n", buf);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcVisibilityParameters - return the current visibility parameters.
 *                            It also sets the current visibility parameters to the list in value.
 */

void pyBotClass::rpcVisibilityParameters (const char *value)
{
  char buf[1024];
  idVec4 param;

  param.Zero ();
  if (protocol_debugging)
    gameLocal.Printf ("rpcVisibilityParameters %s\n", value);
  if (rpcId > 0)
    param = dictionary->visibilityParameters (rpcId, strToidVec4 (value));

  idStr::snPrintf (buf, sizeof (buf), "%f %f %f %f\n",
		   param[0], param[1], param[2], param[3]);
  if (protocol_debugging)
    gameLocal.Printf ("rpcVisibilityParameters responding with: %s\n", buf);
  buffer.pyput (buf);
  state = toWrite;
}


void pyBotClass::rpcFlipVisibility (void)
{
  char buf[1024];
  int result = -1;

  if (protocol_debugging)
    gameLocal.Printf ("rpcFlipVisibility\n");
  if (rpcId > 0)
    result = dictionary->flipVisibility (rpcId);

  idStr::snPrintf (buf, sizeof (buf), "%d\n", result);
  if (protocol_debugging)
    gameLocal.Printf ("rpcFlipVisibility responding with: %s\n", buf);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcVisibilityFlag - return the old visibility flag.
 *                      It also sets the current visibility flag.
 */

void pyBotClass::rpcVisibilityFlag (const char *value)
{
  char buf[1024];
  int flag = 0;

  if (protocol_debugging)
    gameLocal.Printf ("rpcVisibilityFlag %s\n", value);
  if (rpcId > 0)
    flag = dictionary->visibilityFlag (rpcId, atoi (value));

  idStr::snPrintf (buf, sizeof (buf), "%d\n", flag);
  if (protocol_debugging)
    gameLocal.Printf ("rpcVisibilityFlag responding with: %s\n", buf);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcGetSelfEntityNames - return a list of names for the entity of the bot.
 */

void pyBotClass::rpcGetSelfEntityNames (void)
{
  char buf[2048];

  buf[0] = (char)0;
  if (protocol_debugging)
    gameLocal.Printf ("rpcGetSelfEntityNames\n");
  if (rpcId > 0)
    dictionary->getSelfEntityNames (rpcId, buf, sizeof (buf));

  idStr::Append (buf, sizeof (buf), "\n");
  if (protocol_debugging)
    gameLocal.Printf ("rpcGetSelfEntityNames responding with: %s\n", buf);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcSetVisibilityShader - sets the visibilityshader for each entity named.
 *                           data must be:  shadername {entityname}.
 *                           if {entityname} is absent then all entities are changed.
 *                           The bot can only change entities it owns.
 */

void pyBotClass::rpcSetVisibilityShader (char *data)
{
  char buf[2048];
  int flag = -1;

  if (protocol_debugging)
    gameLocal.Printf ("rpcSetVisibilityShader: %s\n", data);
  if (rpcId > 0)
    flag = dictionary->setVisibilityShader (rpcId, data);

  idStr::snPrintf (buf, sizeof (buf), "%d\n", flag);
  if (protocol_debugging)
    gameLocal.Printf ("rpcSetVisibilityShader responding with: %s\n", buf);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcGetClassNameEntity - lookup the number of the entity containing classname, data.
 *                          -1 is returned on failure.
 */

void pyBotClass::rpcGetClassNameEntity (char *data)
{
  char buf[1024];

  if (protocol_debugging)
    gameLocal.Printf ("rpcGetClassNameEntity (%s)\n", data);

  int ent_no = gameLocal.FindEntityFromName (data);

  idStr::snPrintf (buf, sizeof (buf), "%d\n", ent_no);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcGetPairEntity - lookup the number of the entity containing the strings:  a, b.
 *                     arg contains string, a, followed by string, b.
 *                     -1 is returned on failure.
 */

void pyBotClass::rpcGetPairEntity (char *arg)
{
  char buf[1024];
  char *a = arg;

  if (protocol_debugging)
    gameLocal.Printf ("rpcGetPairEntity (%s)\n", arg);

  char *b = index (arg, ' ');
  if (b != NULL)
    {
      *b = (char)0;
      b++;
    }

  int ent_no = gameLocal.FindEntityFromPair (a, b);

  idStr::snPrintf (buf, sizeof (buf), "%d\n", ent_no);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcGetEntityPos - generate an x, y, z string and send it back to the script.
 *                    The parameter, data, contains the entity number.
 */

void pyBotClass::rpcGetEntityPos (char *data)
{
  if (protocol_debugging)
    gameLocal.Printf ("rpcGetEntityPos (%s) call by python\n", data);

  char buf[1024];
  int id = checkId (atoi (data));

  if (id >= 0)
    {
      const idVec3 &org = gameLocal.GetEntityOrigin (id);

      idStr::snPrintf (buf, sizeof (buf), "%g %g %g\n",
		       org.x, org.y, org.z);
    }
  else
    strcpy (buf, "error invalid id sent to getentitypos\n");
  if (protocol_debugging)
    gameLocal.Printf ("rpcGetEntityPos responding with: %s\n", buf);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcGetEntityName - returns the name associated with the entity.
 *                     This is not the "classname" but the "name" in the doom3 map file.
 *                     The parameter, data, contains the entity number.
 */

void pyBotClass::rpcGetEntityName (char *data)
{
  if (protocol_debugging)
    gameLocal.Printf ("rpcGetEntityName (%s) call by python\n", data);

  char buf[1024];
  int id = checkId (atoi (data));

  if (id >= 0)
    {
      idStr::snPrintf (buf, sizeof (buf), "%s\n",
		       gameLocal.GetEntityEntry (id, "name"));
    }
  else
    strcpy (buf, "error invalid id sent to getentityname\n");
  if (protocol_debugging)
    gameLocal.Printf ("rpcGetEntityName responding with: %s\n", buf);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcChangeWeapon - attempt to change weapon to the number in data.
 *                    The amount of ammo is returned.  -1 means no weapon.
 */

void pyBotClass::rpcChangeWeapon (char *data)
{
  if (protocol_debugging)
    gameLocal.Printf ("rpcChangeWeapon (%s) call by python\n", data);

  char buf[1024];
  int weapon = atoi (data);
  int ammo = -1;

  if (weapon >= 0)
    ammo = dictionary->changeWeapon (rpcId, weapon);
  idStr::snPrintf (buf, sizeof (buf), "%d\n", ammo);
  if (protocol_debugging)
    gameLocal.Printf ("rpcChangeWeapon responding with: %s\n", buf);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcDropWeapon - attempt to change weapon to the number in data.
 *                  The amount of ammo is returned.  -1 means no weapon.
 */

void pyBotClass::rpcDropWeapon (void)
{
  if (protocol_debugging)
    gameLocal.Printf ("rpcDropWeapon call by python\n");

  char buf[1024];

  int result = dictionary->dropWeapon (rpcId);
  idStr::snPrintf (buf, sizeof (buf), "%d\n", result);
  if (protocol_debugging)
    gameLocal.Printf ("rpcDropWeapon responding with: %s\n", buf);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcCanSeeEntity - returns 1 if this bot can see entity, entNo,
 *                    returns 0 otherwise.
 */

void pyBotClass::rpcCanSeeEntity (char *data)
{
  if (protocol_debugging)
    gameLocal.Printf ("rpcCanSeeEntity (%s) call by python\n", data);

  char buf[1024];
  int entNo = atoi (data);
  int result = 0;

  if (entNo >= 0)
    result = dictionary->canSeeEntity (rpcId, entNo);
  idStr::snPrintf (buf, sizeof (buf), "%d\n", result);
  if (protocol_debugging)
    gameLocal.Printf ("rpcCanSeeEntity responding with: %s\n", buf);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  rpcMapToRunTimeEntity - given a string containing a decimal number which
 *                          represents the index into the static entity map file.
 *                          Return an index into the dynamic runtime entity array
 *                          which represents the same entity values.
 */

void pyBotClass::rpcMapToRunTimeEntity (char *data)
{
  if (protocol_debugging)
    gameLocal.Printf ("rpcMapToRunTimeEntity (%s) call by python\n", data);

  char buf[1024];
  int entNo = atoi (data);
  int result = 0;

  result = entNo;
  if (entNo >= 0)
    result = gameLocal.MapToRunTimeEntity (entNo);
  idStr::snPrintf (buf, sizeof (buf), "%d\n", result);
  if (protocol_debugging)
    gameLocal.Printf ("rpcMapToRunTimeEntity responding with: %s\n", buf);
  buffer.pyput (buf);
  state = toWrite;
}


/*
 *  writeServer
 */

void pyBotClass::writeServer (bool canBlock)
{
  if (buffer.pyflushed (connectFd, canBlock))
    state = toRead;
}


/*
 *  closeServer
 */

void pyBotClass::closeServer (bool canBlock)
{
  close (connectFd);
  state = toAccept;
}


/*
 *  selectServer
 */

void pyBotClass::selectServer (bool canBlock)
{
  /* currently does nothing.  As we are still waiting for the bot to
     complete some activity.  */
}


/*
 *  selectComplete - if the bot had called select then it will be
 *                   waiting for a reply.  We send true and move to
 *                   the toWrite state.
 */

void pyBotClass::selectComplete (int mask)
{
  if (state == toSelect)
    {
      char buf[1024];

      idStr::snPrintf (buf, sizeof (buf), "%d\n", mask);
      buffer.pyput (buf);
      state = toWrite;
      if (protocol_debugging)
	gameLocal.Printf ("selectComplete (%d)\n", mask);
    }
}


void pyBotClass::poll (bool canBlock, bool dead)
{
  switch (state) {

  case toInit:
    ERROR ("should be done by the superserver");
    break;
  case toAccept:
    acceptServer (canBlock);
    break;
  case toRead:
    readServer (canBlock, dead);
    break;
  case toWrite:
    writeServer (canBlock);
    break;
  case toClose:
    closeServer (canBlock);
    break;
  case toSelect:
    selectServer (canBlock);
    break;
  default:
    ERROR ("unrecognised state");
  }
}


void pyBotClass::forceClose (void)
{
  state = toClose;
}

const char *pyBotClass::getName (void)
{
  return name;
}


void pyBotClass::setName (char *botname)
{
  name = botname;
}
