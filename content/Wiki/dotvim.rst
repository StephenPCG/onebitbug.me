:Title: My Vim Configuration
:Slug: dotvim
:Sidebar: off
:Header: off
:Lang: en

.. raw:: html

    <p><div class="special">
    This post is under ``Wiki`` category, which is more like a personal notes on
    vim usage than a normal blog article. The page may be updated time to time.
    </div></p>

Usage HowTo
===========================

To get the latest code (and with submodules)::

    git clone --recursive https://github.com/StephenPCG/dotvim

To use it temporarily, start vim with ``-u`` option::

    vim -u /path/to/dotvim/vimrc [files ...]

To installed it::

    ln -s /path/to/dotvim/ ~/.vim # or just move it there
    ln -s .vim/vimrc ~/.vimrc     # only for vim older than 7.4

To update plugins::

    git submodule foreach git pull origin master
    git add bundles/
    git commit -m "Update plugins"

Configuration Organization
===========================

vimrc
~~~~~~~

``vimrc`` splits into 4 parts, ``vimrc``, ``functions.vimrc``,
``filetype.vimrc`` and ``personal.vimrc``.

* ``vimrc`` contributes most of the configuration, when any topic is getting
  too large, it will be split out into a single file, like the followings.
* ``functions.vimrc`` contains helper functions used by ``vimrc``.
* ``filetype.vimrc`` contains filetype specific configurations, like what we
  should do with golang source code.
* ``personal.vimrc`` is not managed by git, it contains sensible infomation,
  such as data used in company's coding templete.

plugins
~~~~~~~~~

I use `pathogen <https://github.com/tpope/vim-pathogen>`_ and git
submodules to manage plugins. All plugins are placed in ``bundles/``
directory. If a plugin author does not provide an git repository,
the plugin is copied into ``bundles/`` directory, and needs to be
updated manually later.

To add a plugin::

    git submodule add https://example.com/some/awesome/plugin bundles/awesome-plugin

To remove a plugin::

    git submodule deinit bundles/awesome-plugin
    git rm --cached bundles/awesome-plugin
    rm -r bundles/awesome-plugin

temporary files
~~~~~~~~~~~~~~~~~

Many plugins require a place to store cached data, history and other stuffs.
These data can be deleted safely, and thus no need to be tracked by git.
I tried my best also not to save these data outside of top level directory
of ``dotvim``. Every thing is placed under ``cache/``.

skeletons
~~~~~~~~~~

I use `tskeleton <https://github.com/tomtom/tskeleton_vim>`_
plugin to manage skeletons, all skeletons are placed under ``skeletons/``
directory.

Tips and Tricks
===========================

Using from anywhere
~~~~~~~~~~~~~~~~~~~~~

Sometimes I would like to use my vim configuration on other's computer, or
some servers. It is not poliet to install into other account's ``$HOME/.vim``.
So my vim conf takes relative path in mind when writing. Save dotvim anywhere,
and start with ``vim -u /path/to/dotvim/vimrc``.

Firstly, we should get path of the effective vimrc and use it to form paths
later::

    let g:vimrcroot = fnamemodify(resolve(expand('<sfile>:p')), ':h') . "/"

Commands like ``source``, ``runtime`` does not support variables in command,
so we need to use ``exec``, like::

    exec "source " . g:vimrcroot . "functions.vimrc"

Of course, compared to invoke ``runtime`` directly, we prefer to set
``runtimepath``::

    let &runtimepath = &runtimepath . "," . g:vimrcroot

A helper function is for sourcing files::

    function! Source(file)
      exec "silent! source" . g:vimrcroot . a:file
    endfunction
    ...
    call Source("filetype.vimrc")

Disable plugins temporarily
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Thanks to pathogen's way of managing plugins, we can easily disable a plugin
and tell if a plugin is enabled. To disable a plugin, add it to the
``g:pathogen_disabled`` list, to tell if a plugin is enabled, just check if
it exists in ``bundles/`` directory and not in ``g:pathogen_disabled``.

Two helper functions is created::

    function! DisablePlugin(plugin)
      if !exists("g:pathogen_disabled")
        let g:pathogen_disabled = []
      endif
      let g:pathogen_disabled += [a:plugin]
    endfunction
    
    function! IsPluginEnabled(plugin)
        if finddir(a:plugin, expand(g:vimrcroot . "bundles/")) != "" && (index(g:pathogen_disabled, a:plugin) < 0)
            return 1 | else | return 0 | endif
    endfuncti

We can disable plugins automatically based on running environment.
For example, there are two seperate complete engine ``neocomplcache``
and ``neocomplete``, the later is faster but require ``lua`` feature.
Only one is need at a given time, so we can choose which to use::

    if has("lua")
      call DisablePlugin("neocomplcache")
    else
      call DisablePlugin("neocomplete")
    endif

We can also enable settings based on what plugins is installed.
Say which snippets to be used by snip engine ``neosnippet``.
I prefer to use ``vim-snippets`` if it is enabled::

    if IsPluginEnabled("vim-snippets")
      let g:neosnippet#snippets_directory = g:vimrcroot . 'bundles/vim-snippets/snippets'
    endif

Use <C-L> to clear highlights
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We can use ``:set nohls`` to clear search highlights, but it requires much
typing. We can use ``ctrl-l`` which is designed to redraw screen to do this.::

    if maparg('<C-L>', 'n') ==# ''
      nnoremap <silent> <C-L> :nohlsearch<CR><C-L>
    endif

Use <C-Z> to open shell
~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, when ``<C-Z>`` is preseed, the shell will put vim into backgroud,
and recall it when we invoke ``fg``. I am too lazy to type ``fg<cr>`` each time,
I always prefer to use a single hand to finish this task, with ``^D``.
So I bind ``<C-Z>`` to open external shell as vim's subprocess.::

    nmap <C-Z> :shell<cr>

Binding <M-> keys in terminals
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Many terms send ``^[X`` (two characters, ``^[`` is for ``<esc>``) when ``Alt-X``
is pressed. So to make a ``<M-X>`` binding, we have to bind ``<esc>X`` for
such terminals, and ``<M-X>`` for other terms (and GUI versions of vim).
Setting up two binding is not the painful stuff, Use ``<esc>`` in binding will
cause a ``timeoutlen`` latency when you pressed ``<esc>`` trying to return to
normal mode. People struggles waiting or pressing ``<esc>>`` twice at once.

I found a perfect solution from
`lilydjwg <://github.com/lilydjwg/dotvim/blob/master/plugin/escalt.vim>`_.
The key point is to change keycode of ``<M-X>`` to ``^[X``, so vim will use
``ttimeoutlen`` to wait for the rest part, rather than painful ``timeoutlen``.

Download the raw
`escalt.vim <https://github.com/lilydjwg/dotvim/blob/master/plugin/escalt.vim>`_
and save as ``bundles/escalt/plugins/escalt.vim``. And it just works!

.. raw:: html

   <p><div class="warning">
   Warning! Don't try to copy the file content from browser and paste into editor,
   the file contains many nonprinting characters.
   </div></p>

Resources
===========================

There are many great vim resources.

* `vimcasts.org <http://vimcasts.org/>`_ creates a great collections of vim
  screencasts, can be subscribed with podcasts.
* `Tim Pope <https://github.com/tpope/>`_ is great at vim plugins, most of
  his plugins are useful.
* `usevim.com <http://usevim.com/>`_ collects practical vim plugins.
