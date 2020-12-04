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

Author:  Gaius Mulley  <gaius.southwales@gmail.com>
*/

#if !defined(PYBOT_H)
# define PYBOT_H
# if defined(PYBOT_C)
#   define EXTERN
# else
#   define EXTERN extern
# endif

#define S(x) #x
#define S_(x) S(x)
#define S__LINE__ S_(__LINE__)

EXTERN void initSuperServer (void);

#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netdb.h>

#include "idlib/math/Vector.h"

class idAI;
class idPlayer;

enum serverState { toInit, toAccept, toRead, toWrite, toWriteConnected, toSelect, toClose };

#define MAX_PY_BUFFER 4096


class pyBufferClass
{
public:
  pyBufferClass (void);
  ~pyBufferClass (void);
  pyBufferClass (const pyBufferClass &from);

  char *pyread (int fd, bool canBlock);
  void pyput (char *output);
  void pyputChar (char ch);
  bool pyflushed (int fd, bool canBlock);
private:
  int rin;
  char rBuffer[MAX_PY_BUFFER+1];
  int win;
  int wout;
  int wsize;
  char wBuffer[MAX_PY_BUFFER];
};


class pyBotClass
{
 public:
  pyBotClass (void);
  ~pyBotClass (void);
  pyBotClass (const pyBotClass &from);

  void initServer (int desiredPort);
  void setName (char *botname);
  const char *getName (void);
  void poll (bool canBlock, bool dead);
  void selectComplete (int mask);
  bool getConnected (void);
  void setConnected (void);
  int getPortNo (void);
  int getRpcId (void);
  void setRpcId (int);
  int getInstanceId (void);
  void setInstanceId (int);
  void forceClose (void);
 private:
  int tryActivate (int desiredPort);
  void acceptServer (bool canBlock);
  void registerServer (bool canBlock);
  void readServer (bool canBlock, bool dead);
  void closeServer (bool canBlock);
  void interpretRemoteProcedureCall (char *data);
  void writeServer (bool canBlock);
  void selectServer (bool canBlock);
  void rpcSuper (void);
  void rpcGetPos (char *data);
  void rpcSelf (void);
  void rpcHealth (void);
  void rpcMaxObj (void);
  void rpcStep (char *data);
  void rpcRight (char *data);
  void rpcForward (char *data);
  void rpcStepVec (char *data);
  void rpcAim (char *data);
  void rpcStartFiring (void);
  void rpcStopFiring (void);
  void rpcReloadWeapon (void);
  void rpcAmmo (const char *data);
  void rpcStepUp (char *data);
  void rpcTurn (char *data);
  void rpcAngle (void);
  char *truncstr (char *name);
  void rpcTag (char *name);
  void rpcSelect (char *data);
  void rpcGetClassNameEntity (char *data);
  void rpcGetPairEntity (char *arg);
  void rpcGetEntityPos (char *data);
  void rpcChangeWeapon (char *data);
  void rpcGetEntityName (char *data);
  void rpcCanSeeEntity (char *data);
  void rpcMapToRunTimeEntity (char *data);
  void rpcVisibility (const char *value);
  void rpcVisibilityFlag (const char *value);
  void rpcGetSelfEntityNames (void);
  void rpcSetVisibilityShader (char *data);
  void rpcVisibilityParameters (const char *value);
  void rpcFlipVisibility (void);
  void rpcInventoryWeapon (const char *weapon_number);
  void rpcDropWeapon (void);
  idVec4 strToidVec4 (const char *value);
  int instanceId;  // python class, instance id
  int rpcId;  // index into the rpc array
  char *name;
  int portNo;
  bool enabled;
  pyBufferClass buffer;
  serverState state;
  struct sockaddr_in sa;
  struct sockaddr_in isa;
  int socketFd;
  int connectFd;
  bool connected;
};


class pyServerClass
{
 public:
  pyServerClass (void);
  ~pyServerClass (void);
  pyServerClass (const pyServerClass &from);

  void poll (bool canBlock);
 private:
  void initServer (void);
  int tryActivate (int desiredPort);
  void acceptServer (bool canBlock);
  void readServer (bool canBlock);
  void writeServer (bool canBlock);
  void writeConnectedServer (bool canBlock);
  void closeServer (bool canBlock);
  void rpcSuper (void);
  void interpretRemoteProcedureCall (char *data);
  bool enabled;
  pyBufferClass buffer;
  serverState state;
  struct sockaddr_in sa;
  struct sockaddr_in isa;
  int socketFd;
  int connectFd;
  pyBotClass *connectedBot;
};


/*
 *  registerName - the map has requested a Python bot.
 *                 We create a server and tell the super server
 *                 which port we are using.
 *                 This bot is completely controlled via Python
 *                 and the doom3 AI is disabled.
 */

EXTERN pyBotClass *registerName (const char *name, idAI *idBot, int instance);


/*
 *  registerName - the map has requested a Python bot.
 *                 We create a server and tell the super server
 *                 which port we are using.
 *                 This bot is completely controlled via Python
 *                 and no user input is used.
 */

EXTERN pyBotClass *registerName (const char *name, idPlayer *idBot, int instance);


/*
 *  lookupName - returns the pyBotClass associated with, name, and, instance.
 */

EXTERN pyBotClass *lookupName (const char *name, int instance);

/*
 *  deRegisterName - the bot has died and we need to deregister its name.
 */

EXTERN pyBotClass *deRegisterName (const char *name, idPlayer *idBot, int instance);


/*
 *  populateDictionary - adds idBot into the python bot universe of objects.
 *                       This bot is controlled by the doom3 AI.
 */

EXTERN void populateDictionary (const char *name, idAI *idBot, int instance);


/*
 *  populateDictionary - adds player ip into the python bot universe of objects.
 */

EXTERN void populateDictionary (const char *name, idPlayer *ip, int instance);

#endif
