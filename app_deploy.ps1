# https://devcenter.heroku.com/articles/container-registry-and-runtime
 #>

# log in to heroku
heroku login

# create dyno/instance/whatever  (no need to do after first time)
heroku create


# change stack to container for docker deploy  (no need to do after first time)
heroku stack:set container

# log in to container registry
heroku container:login

# The above commands we only do the first time then we can deploy as much we like


# "worker" is the process type. Still not 100% clear on what options are avaiable or what they mean contextually
heroku container:push worker -a

# create a "release"
heroku container:release worker -a


# Post install maintenance commands



# check the logs
# https://devcenter.heroku.com/articles/logging
heroku logs -a hidden-springs-38177
heroku logs -a hidden-springs-38177 -n 200
heroku logs -a hidden-springs-38177 --tail

# list apps
heroku apps

# restart dyno
heroku dyno:restart -a hidden-springs-38177



