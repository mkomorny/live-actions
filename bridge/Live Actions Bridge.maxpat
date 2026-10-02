{
	"patcher": {
		"fileversion": 1,
		"appversion": {
			"major": 9,
			"minor": 0,
			"revision": 10,
			"architecture": "x64",
			"modernui": 1
		},
		"classnamespace": "box",
		"rect": [80.0, 80.0, 640.0, 360.0],
		"openrect": [0.0, 0.0, 420.0, 56.0],
		"default_fontsize": 10.0,
		"default_fontname": "Ableton Sans Medium",
		"gridsize": [8.0, 8.0],
		"openinpresentation": 1,
		"autosave": 0,
		"devicewidth": 420.0,
		"description": "Live Actions device. Drop it on any audio track. Audio passes through.",
		"digest": "Talks to the Live Actions desktop app and the Live Object Model.",
		"tags": "live actions, max for live",
		"style": "",
		"boxes": [
			{
				"box": {
					"id": "c-title",
					"maxclass": "comment",
					"patching_rect": [8.0, 300.0, 160.0, 18.0],
					"presentation": 1,
					"presentation_rect": [8.0, 4.0, 148.0, 18.0],
					"numinlets": 1,
					"numoutlets": 0,
					"outlettype": [],
					"parameter_enable": 0,
					"text": "Live Actions",
					"fontsize": 13.0,
					"fontname": "Ableton Sans Medium",
					"textcolor": [0.82, 0.82, 0.82, 1.0]
				}
			},
			{
				"box": {
					"id": "obj-status",
					"maxclass": "textedit",
					"patching_rect": [200.0, 110.0, 360.0, 22.0],
					"presentation": 1,
					"presentation_rect": [8.0, 24.0, 404.0, 16.0],
					"numinlets": 1,
					"numoutlets": 4,
					"outlettype": ["", "int", "", ""],
					"fontsize": 10.0,
					"border": 0,
					"keymode": 1,
					"outputmode": 1,
					"readonly": 1,
					"varname": "status"
				}
			},
			{
				"box": {
					"id": "obj-open",
					"maxclass": "textbutton",
					"text": "Open desktop host",
					"mode": 0,
					"patching_rect": [220.0, 70.0, 160.0, 22.0],
					"presentation": 1,
					"presentation_rect": [220.0, 4.0, 192.0, 20.0],
					"numinlets": 1,
					"numoutlets": 3,
					"outlettype": ["", "", "int"],
					"fontsize": 10.0,
					"fontname": "Ableton Sans Medium",
					"bgcolor": [0.23, 0.51, 0.96, 1.0],
					"bgoncolor": [0.16, 0.38, 0.75, 1.0],
					"textcolor": [1.0, 1.0, 1.0, 1.0],
					"textoncolor": [1.0, 1.0, 1.0, 1.0],
					"rounded": 4.0,
					"parameter_enable": 0
				}
			},
			{
				"box": {
					"id": "msg-openhost",
					"maxclass": "message",
					"text": "openhost",
					"patching_rect": [220.0, 100.0, 70.0, 22.0],
					"numinlets": 2,
					"numoutlets": 1,
					"outlettype": [""],
					"fontsize": 10.0
				}
			},
			{
				"box": {
					"id": "c-ports",
					"maxclass": "comment",
					"patching_rect": [176.0, 300.0, 236.0, 18.0],
					"presentation": 0,
					"numinlets": 1,
					"numoutlets": 0,
					"outlettype": [],
					"parameter_enable": 0,
					"text": "UDP 11924 in / 11925 out",
					"fontsize": 10.0,
					"fontname": "Ableton Sans Medium",
					"textcolor": [0.55, 0.55, 0.55, 1.0]
				}
			},
			{
				"box": {
					"id": "c-help",
					"maxclass": "comment",
					"text": "Keep live-actions-bridge.js next to this device. live.thisdevice bangs init. Do not use LiveAPI in loadbang. Audio passes through.",
					"patching_rect": [20.0, 20.0, 520.0, 32.0],
					"fontsize": 11.0,
					"numinlets": 1,
					"numoutlets": 0,
					"outlettype": [],
					"presentation": 0
				}
			},
			{
				"box": {
					"id": "obj-this",
					"maxclass": "newobj",
					"text": "live.thisdevice",
					"patching_rect": [20.0, 70.0, 110.0, 22.0],
					"numinlets": 1,
					"numoutlets": 2,
					"outlettype": ["", ""],
					"fontsize": 10.0,
					"fontname": "Ableton Sans Medium"
				}
			},
			{
				"box": {
					"id": "obj-defer",
					"maxclass": "newobj",
					"text": "deferlow",
					"patching_rect": [20.0, 92.0, 50.0, 22.0],
					"numinlets": 1,
					"numoutlets": 1,
					"outlettype": [""],
					"fontsize": 10.0,
					"fontname": "Ableton Sans Medium"
				}
			},
			{
				"box": {
					"id": "obj-js",
					"maxclass": "newobj",
					"text": "js live-actions-bridge.js",
					"patching_rect": [20.0, 118.0, 170.0, 22.0],
					"numinlets": 1,
					"numoutlets": 2,
					"outlettype": ["", ""],
					"fontsize": 10.0,
					"saved_object_attributes": {
						"filename": "live-actions-bridge.js",
						"parameter_enable": 0,
						"autowatch": 1
					}
				}
			},
			{
				"box": {
					"id": "obj-udp-in",
					"maxclass": "newobj",
					"text": "udpreceive 11924",
					"patching_rect": [20.0, 150.0, 200.0, 22.0],
					"numinlets": 1,
					"numoutlets": 1,
					"outlettype": [""],
					"fontsize": 10.0,
					"fontname": "Ableton Sans Medium"
				}
			},
			{
				"box": {
					"id": "obj-udp-out",
					"maxclass": "newobj",
					"text": "udpsend 127.0.0.1 11925",
					"patching_rect": [20.0, 190.0, 170.0, 22.0],
					"numinlets": 1,
					"numoutlets": 0,
					"outlettype": [],
					"fontsize": 10.0,
					"fontname": "Ableton Sans Medium"
				}
			},
			{
				"box": {
					"id": "obj-plugin",
					"maxclass": "newobj",
					"text": "plugin~",
					"patching_rect": [280.0, 150.0, 60.0, 22.0],
					"numinlets": 2,
					"numoutlets": 2,
					"outlettype": ["signal", "signal"],
					"fontsize": 10.0,
					"fontname": "Ableton Sans Medium"
				}
			},
			{
				"box": {
					"id": "obj-plugout",
					"maxclass": "newobj",
					"text": "plugout~",
					"patching_rect": [280.0, 190.0, 70.0, 22.0],
					"numinlets": 2,
					"numoutlets": 2,
					"outlettype": ["signal", "signal"],
					"fontsize": 10.0,
					"fontname": "Ableton Sans Medium"
				}
			}
		],
		"lines": [
			{
				"patchline": {
					"source": ["obj-this", 0],
					"destination": ["obj-defer", 0]
				}
			},
			{
				"patchline": {
					"source": ["obj-defer", 0],
					"destination": ["obj-js", 0]
				}
			},
			{
				"patchline": {
					"source": ["obj-udp-in", 0],
					"destination": ["obj-js", 0]
				}
			},
			{
				"patchline": {
					"source": ["obj-js", 0],
					"destination": ["obj-udp-out", 0]
				}
			},
			{
				"patchline": {
					"source": ["obj-js", 1],
					"destination": ["obj-status", 0]
				}
			},
			{
				"patchline": {
					"source": ["obj-open", 0],
					"destination": ["msg-openhost", 0]
				}
			},
			{
				"patchline": {
					"source": ["msg-openhost", 0],
					"destination": ["obj-js", 0]
				}
			},
			{
				"patchline": {
					"source": ["obj-plugin", 0],
					"destination": ["obj-plugout", 0]
				}
			},
			{
				"patchline": {
					"source": ["obj-plugin", 1],
					"destination": ["obj-plugout", 1]
				}
			}
		],
		"dependency_cache": [
			{
				"name": "live-actions-bridge.js",
				"bootpath": ".",
				"type": "TEXT",
				"implicit": 1
			},
			{
				"name": "live-actions-pal.js",
				"bootpath": ".",
				"type": "TEXT",
				"implicit": 1
			}
		],
		"project": {
			"version": 1,
			"creationdate": 3590052493,
			"modificationdate": 3590052493,
			"viewrect": [25.0, 124.0, 300.0, 500.0],
			"autoorganize": 1,
			"hideprojectwindow": 1,
			"showdependencies": 1,
			"autolocalize": 0,
			"contents": {
				"patchers": {}
			},
			"layout": {},
			"searchpath": {},
			"detailsvisible": 0,
			"amxdtype": 1633771873,
			"readonly": 0,
			"devpathtype": 0,
			"devpath": ".",
			"sortmode": 0,
			"viewmode": 0,
			"includepackages": 0
		}
	}
}
